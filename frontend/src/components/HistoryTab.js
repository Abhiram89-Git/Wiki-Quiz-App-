import React, { useState, useEffect } from 'react';
import QuizDisplay from './QuizDisplay';
import LoadingSpinner from './LoadingSpinner';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function HistoryTab() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedQuiz, setSelectedQuiz] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await fetch(`${API_URL}/api/history`);
      if (!response.ok) throw new Error('Failed to fetch history');
      
      const data = await response.json();
      setHistory(data);
    } catch (err) {
      setError(err.message || 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (quizId) => {
    try {
      setLoading(true);
      setError('');
      
      const response = await fetch(`${API_URL}/api/quiz/${quizId}`);
      if (!response.ok) throw new Error('Failed to fetch quiz details');
      
      const data = await response.json();
      setSelectedQuiz(data);
    } catch (err) {
      setError(err.message || 'Failed to load quiz');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteQuiz = async (quizId) => {
    if (!window.confirm('Are you sure you want to delete this quiz?')) return;

    try {
      const response = await fetch(`${API_URL}/api/quiz/${quizId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) throw new Error('Failed to delete quiz');
      
      setHistory(history.filter(h => h.id !== quizId));
    } catch (err) {
      setError(err.message || 'Failed to delete quiz');
    }
  };

  const handleBackToHistory = () => {
    setSelectedQuiz(null);
    fetchHistory();
  };

  if (selectedQuiz) {
    return (
      <div className="history-details">
        <button
          onClick={handleBackToHistory}
          className="button button-secondary back-button"
        >
          ← Back to History
        </button>
        <QuizDisplay quizData={selectedQuiz} />
      </div>
    );
  }

  if (loading && history.length === 0) {
    return <LoadingSpinner />;
  }

  return (
    <div className="history-tab">
      <div className="history-header card">
        <h2>📚 Past Quizzes ({history.length})</h2>
        <button
          onClick={fetchHistory}
          className="button button-secondary"
          disabled={loading}
        >
          {loading ? 'Refreshing...' : '🔄 Refresh'}
        </button>
      </div>

      {error && <div className="error-message">⚠️ {error}</div>}

      {history.length === 0 ? (
        <div className="empty-state card">
          <p>📭 No quizzes generated yet.</p>
          <p>Go to the "Generate Quiz" tab to create your first quiz!</p>
        </div>
      ) : (
        <div className="history-table-container">
          <table className="history-table">
            <thead>
              <tr>
                <th>Article Title</th>
                <th>URL</th>
                <th>Generated On</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item) => (
                <tr key={item.id} className="history-row">
                  <td className="title-cell">{item.title}</td>
                  <td className="url-cell">
                    <a href={item.url} target="_blank" rel="noopener noreferrer">
                      View →
                    </a>
                  </td>
                  <td className="date-cell">
                    {new Date(item.created_at).toLocaleDateString()} 
                    <br/>
                    <span className="time">{new Date(item.created_at).toLocaleTimeString()}</span>
                  </td>
                  <td className="actions-cell">
                    <button
                      onClick={() => handleViewDetails(item.id)}
                      className="action-button details-button"
                      title="View full quiz"
                    >
                      Details
                    </button>
                    <button
                      onClick={() => handleDeleteQuiz(item.id)}
                      className="action-button delete-button"
                      title="Delete quiz"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default HistoryTab;