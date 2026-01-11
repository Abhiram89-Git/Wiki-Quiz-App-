import React, { useState, useRef } from 'react';
import QuizDisplay from './QuizDisplay';
import LoadingSpinner from './LoadingSpinner';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function GenerateQuizTab() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [quizData, setQuizData] = useState(null);
  const [error, setError] = useState('');
  const [urlPreview, setUrlPreview] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const scrollRef = useRef(null);

  // Validate URL format
  const isValidUrl = (urlString) => {
    try {
      return urlString.startsWith('https://en.wikipedia.org/wiki/');
    } catch {
      return false;
    }
  };

  // Fetch URL preview (bonus feature)
  const handlePreviewUrl = async () => {
    if (!isValidUrl(url)) {
      setError('Please enter a valid Wikipedia URL');
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      const response = await fetch(`${API_URL}/api/validate-url?url=${encodeURIComponent(url)}`);
      const data = await response.json();

      if (data.valid) {
        setUrlPreview(data.title);
        setShowPreview(true);
      } else {
        setError(data.message || 'Invalid Wikipedia URL');
      }
    } catch (err) {
      setError('Failed to validate URL. Check your connection.');
    } finally {
      setLoading(false);
    }
  };

  // Generate quiz
  const handleGenerateQuiz = async () => {
    if (!isValidUrl(url)) {
      setError('Please enter a valid Wikipedia URL (https://en.wikipedia.org/wiki/...)');
      return;
    }

    try {
      setLoading(true);
      setError('');
      setQuizData(null);

      const response = await fetch(`${API_URL}/api/generate-quiz`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate quiz');
      }

      const data = await response.json();
      setQuizData(data);
      
      // Scroll to results
      setTimeout(() => {
        scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      setError(err.message || 'An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setUrl('');
    setQuizData(null);
    setError('');
    setUrlPreview(null);
    setShowPreview(false);
  };

  return (
    <div className="generate-quiz-tab">
      {/* Input Section */}
      <div className="input-section card">
        <h2>Enter Wikipedia Article URL</h2>
        
        <div className="url-input-group">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://en.wikipedia.org/wiki/Alan_Turing"
            className="url-input"
            disabled={loading}
          />
          <button
            onClick={handlePreviewUrl}
            className="button button-secondary"
            disabled={!url || loading}
          >
            {loading ? 'Checking...' : 'Preview'}
          </button>
        </div>

        {/* URL Preview */}
        {showPreview && urlPreview && (
          <div className="preview-box">
            <span className="checkmark">✓</span>
            <div>
              <p className="preview-label">Article Found</p>
              <p className="preview-title">{urlPreview}</p>
            </div>
          </div>
        )}

        {error && <div className="error-message">⚠️ {error}</div>}

        {/* Action Buttons */}
        <div className="button-group">
          <button
            onClick={handleGenerateQuiz}
            className="button button-primary"
            disabled={!url || loading}
          >
            {loading ? 'Generating...' : '🚀 Generate Quiz'}
          </button>
          {quizData && (
            <button
              onClick={handleReset}
              className="button button-secondary"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Loading Spinner */}
      {loading && <LoadingSpinner />}

      {/* Quiz Results */}
      {quizData && (
        <div ref={scrollRef} className="quiz-results">
          <QuizDisplay quizData={quizData} />
        </div>
      )}
    </div>
  );
}

export default GenerateQuizTab;