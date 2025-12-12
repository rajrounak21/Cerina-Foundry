"""
Cerina - AI CBT Exercise Creator
Flask web application integrating LangGraph multi-agent workflow with:
- Session history
- Real-time agent streaming
- Human-in-the-loop interruptions
- Thread-safe PostgreSQL persistence
"""

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from graph_builder import build_graph
from state import AgentState
from checkpoint_store import get_checkpointer_context, get_pool
import traceback
import json
from datetime import datetime

app = Flask(__name__)

# Note: We do NOT build a global graph anymore because checkpointers 
# need to be scoped per-request for thread safety with Postgres.

@app.route('/')
def index():
    """Render the main UI"""
    return render_template('index.html')


@app.route('/sessions', methods=['GET'])
def get_sessions():
    """
    Get all session history from session_metadata table
    """
    try:
        pool = get_pool()
        sessions = []
        
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # Get sessions from our dedicated metadata table
                cur.execute("""
                    SELECT thread_id, title, created_at
                    FROM session_metadata 
                    ORDER BY created_at DESC
                """)
                rows = cur.fetchall()
                
                for row in rows:
                    thread_id, title, created_at = row
                    sessions.append({
                        'id': thread_id,
                        'timestamp': created_at.isoformat() if created_at else None,
                        'query': title or f"Session {thread_id[-8:]}" 
                    })

        return jsonify({'sessions': sessions})
    except Exception as e:
        print(f"Error in /sessions: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return jsonify({'sessions': []})

@app.route('/generate', methods=['POST'])
def generate():
    """
    Generate a new CBT exercise from user query (Synchronous Fallback)
    """
    try:
        data = request.get_json()
        user_query = data.get('user_query', '').strip()
        thread_id = data.get('thread_id', 'default-thread')
        
        if not user_query:
            return jsonify({'error': 'No query provided'}), 400

        # Save session metadata
        try:
            pool = get_pool()
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO session_metadata (thread_id, title) VALUES (%s, %s) ON CONFLICT (thread_id) DO NOTHING",
                        (thread_id, user_query[:100])
                    )
        except Exception as e:
            print(f"Failed to save session metadata: {e}")
        
        # Initial state
        initial_state = {
            "user_query": user_query,
            "draft": "",
            "previous_drafts": [],
            "safety_notes": [],
            "critic_notes": [],
            "metadata": {
                "iterations": 0, "safety_pass": True, "critic_pass": True,
                "user_rejected": False, "edited_by_user": False
            },
            "final_output": "", "user_action": "", "edited_text": ""
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Use thread-safe checkpointer
        with get_checkpointer_context() as checkpointer:
            graph = build_graph(checkpointer)
            result = graph.invoke(initial_state, config=config)
        
        # Extract response
        response_data = {
            'draft': result.get('draft', ''),
            'iterations': result.get('metadata', {}).get('iterations', 0),
            'safety_pass': result.get('metadata', {}).get('safety_pass', True),
            'critic_pass': result.get('metadata', {}).get('critic_pass', True),
            'safety_notes': result.get('safety_notes', []),
            'critic_notes': result.get('critic_notes', []),
            'final_output': result.get('final_output', ''),
            'next_node': result.get('metadata', {}).get('next_node', ''),
            'thread_id': thread_id
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in /generate: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/stream', methods=['POST'])
def stream_generate():
    """
    Stream the generation process
    """
    try:
        data = request.get_json()
        user_query = data.get('user_query', '').strip()
        thread_id = data.get('thread_id', 'default-thread')
        
        # Save session metadata for stream requests too
        try:
            pool = get_pool()
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO session_metadata (thread_id, title) VALUES (%s, %s) ON CONFLICT (thread_id) DO NOTHING",
                        (thread_id, user_query[:100])
                    )
        except Exception as ex:
             print(f"Failed to save session metadata (stream): {ex}")

    except Exception as e:
        return jsonify({'error': f"Invalid request: {str(e)}"}), 400

    def generate_stream(query, tid):
        try:
            if not query:
                yield f"data: {json.dumps({'error': 'No query provided'})}\n\n"
                return
            
            print(f"Starting stream for thread {tid}")
            
            initial_state = {
                "user_query": query,
                "draft": "",
                "previous_drafts": [],
                "safety_notes": [],
                "critic_notes": [],
                "metadata": {
                    "iterations": 0, "safety_pass": True, "critic_pass": True,
                    "user_rejected": False, "edited_by_user": False
                },
                "final_output": "", "user_action": "", "edited_text": ""
            }
            
            config = {"configurable": {"thread_id": tid}}
            
            with get_checkpointer_context() as checkpointer:
                graph = build_graph(checkpointer)
                
                print("Invoking graph stream...")
                step_count = 0
                for event in graph.stream(initial_state, config=config):
                    step_count += 1
                    event_data = {
                        'type': 'node_complete',
                        'data': event,
                        'timestamp': datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
            
            print(f"Stream complete, steps: {step_count}")
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            
        except Exception as e:
            print(f"Stream error: {e}")
            traceback.print_exc()
            error_data = {'type': 'error', 'error': str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return Response(stream_with_context(generate_stream(user_query, thread_id)), mimetype='text/event-stream')

@app.route('/action', methods=['POST'])
def handle_action():
    """
    Handle user actions: approve, edit, or reject
    """
    try:
        data = request.get_json()
        thread_id = data.get('thread_id', 'default-thread')
        action = data.get('action') 
        edited_text = data.get('edited_text', '')
        
        if not action:
            return jsonify({'error': 'No action specified'}), 400
        
        config = {"configurable": {"thread_id": thread_id}}
        
        with get_checkpointer_context() as checkpointer:
            graph = build_graph(checkpointer)
            
            # Get the last state
            state_snapshot = graph.get_state(config)
            current_state = state_snapshot.values
            
            # Update state
            updated_state = dict(current_state)
            updated_state['user_action'] = action
            if action == 'edit':
                updated_state['edited_text'] = edited_text
            
            # Continue execution
            result = graph.invoke(updated_state, config=config)
        
        result_dict = result if isinstance(result, dict) else result.dict()
        
        if action == 'approve' and result_dict.get('final_output', '') != '':
            # Save to dedicated results table
            try:
                pool = get_pool()
                with pool.connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO saved_exercises (thread_id, query, content) VALUES (%s, %s, %s)",
                            (thread_id, result_dict.get('user_query', ''), result_dict.get('final_output'))
                        )
            except Exception as e:
                print(f"Failed to save exercise: {e}")

        
        response_data = {
            'draft': result_dict.get('draft', ''),
            'iterations': result_dict.get('metadata', {}).get('iterations', 0),
            'safety_pass': result_dict.get('metadata', {}).get('safety_pass', True),
            'critic_pass': result_dict.get('metadata', {}).get('critic_pass', True),
            'safety_notes': result_dict.get('safety_notes', []),
            'critic_notes': result_dict.get('critic_notes', []),
            'final_output': result_dict.get('final_output', ''),
            'next_node': result_dict.get('metadata', {}).get('next_node', ''),
            'approved': action == 'approve' and result_dict.get('final_output', '') != ''
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in /action: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/history/<thread_id>', methods=['GET'])
def get_thread_history(thread_id):
    """
    Get the full history of a specific thread/session
    """
    try:
        config = {"configurable": {"thread_id": thread_id}}
        
        with get_checkpointer_context() as checkpointer:
            graph = build_graph(checkpointer)
            state_snapshot = graph.get_state(config)
            
            history = []
            if state_snapshot.values:
                history.append({
                    'state': state_snapshot.values,
                    'timestamp': datetime.now().isoformat()
                })
        
        return jsonify({
            'thread_id': thread_id,
            'history': history
        })
        
    except Exception as e:
        print(f"Error in /history: {str(e)}")
        return jsonify({'error': str(e)}), 500
@app.route('/sessions/<thread_id>', methods=['DELETE'])
def delete_session(thread_id):
    try:
        pool = get_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # Cleanup all tables
                tables = ['checkpoints', 'checkpoint_blobs', 'checkpoint_writes', 'saved_exercises', 'session_metadata']
                for table in tables:
                    try:
                        cur.execute(f"DELETE FROM {table} WHERE thread_id = %s", (thread_id,))
                    except Exception:
                        conn.rollback()
                        continue
        return jsonify({'status': 'deleted', 'id': thread_id})
    except Exception as e:
        print(f"Error deleting session {thread_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'Cerina CBT Generator'})

if __name__ == '__main__':
    try:
        pool = get_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # Ensure saved_exercises exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS saved_exercises (
                        id SERIAL PRIMARY KEY,
                        thread_id TEXT NOT NULL,
                        query TEXT,
                        content TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                # Create session_metadata table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS session_metadata (
                        thread_id TEXT PRIMARY KEY,
                        title TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
        print("✅ DB Connection Pool Initialized & Tables Verified")
    except Exception as e:
        print(f"⚠️ DB Setup Failed: {e}")

    print("🚀 Starting Cerina - AI CBT Exercise Creator")
    print("📍 Server running at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
