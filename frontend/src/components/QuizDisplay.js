import React, { useState } from 'react';
import QuizMode from './QuizMode';

function QuizDisplay({ quizData }) {
  const [showTakeQuiz, setShowTakeQuiz] = useState(false);
  const [activeSection, setActiveSection] = useState(null);

  const getDifficultyColor = (difficulty) => {
    const colors = {
      easy: '#4CAF50',
      medium: '#FFC107',
      hard: '#F44336',
    };
    return colors[difficulty] || '#2196F3';
  };

  if (showTakeQuiz) {
    return (
      <>
        <button
          onClick={() => setShowTakeQuiz(false)}
          className="button button-secondary back-button"
        >
          ← Back to Preview
        </button>
        <QuizMode quizData={quizData} />
      </>
    );
  }

  return (
    <div className="quiz-display">
      {/* Header */}
      <div className="quiz-header card">
        <h1>{quizData.title}</h1>
        <a href={quizData.url} target="_blank" rel="noopener noreferrer" className="wiki-link">
          View on Wikipedia →
        </a>
      </div>

      {/* Summary */}
      <div className="summary-section card">
        <h2>📖 Summary</h2>
        <p className="summary-text">{quizData.summary}</p>
      </div>

      {/* Key Entities */}
      <div className="entities-section card">
        <h2>🏷️ Key Entities</h2>
        <div className="entities-grid">
          {quizData.key_entities.people?.length > 0 && (
            <div className="entity-group">
              <h4>People</h4>
              <ul>
                {quizData.key_entities.people.map((person, idx) => (
                  <li key={idx}>{person}</li>
                ))}
              </ul>
            </div>
          )}
          {quizData.key_entities.organizations?.length > 0 && (
            <div className="entity-group">
              <h4>Organizations</h4>
              <ul>
                {quizData.key_entities.organizations.map((org, idx) => (
                  <li key={idx}>{org}</li>
                ))}
              </ul>
            </div>
          )}
          {quizData.key_entities.locations?.length > 0 && (
            <div className="entity-group">
              <h4>Locations</h4>
              <ul>
                {quizData.key_entities.locations.map((loc, idx) => (
                  <li key={idx}>{loc}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Quiz Preview */}
      <div className="quiz-section card">
        <div className="quiz-header-row">
          <h2>❓ Quiz Questions ({quizData.quiz.length})</h2>
          <button
            onClick={() => setShowTakeQuiz(true)}
            className="button button-primary"
          >
            Take Quiz Mode
          </button>
        </div>

        <div className="quiz-questions">
          {quizData.quiz.map((question, idx) => (
            <div key={idx} className="question-card">
              <div className="question-header">
                <span className="question-number">Q{idx + 1}</span>
                <span
                  className="difficulty-badge"
                  style={{ backgroundColor: getDifficultyColor(question.difficulty) }}
                >
                  {question.difficulty}
                </span>
              </div>

              <p className="question-text">{question.question}</p>

              <div className="options-list">
                {question.options.map((option, optIdx) => {
                  const letter = String.fromCharCode(65 + optIdx);
                  const isCorrect = option === question.answer;
                  return (
                    <div
                      key={optIdx}
                      className={`option ${isCorrect ? 'correct-answer' : ''}`}
                    >
                      <span className="option-letter">{letter}</span>
                      <span className="option-text">{option}</span>
                      {isCorrect && <span className="checkmark">✓</span>}
                    </div>
                  );
                })}
              </div>

              <div className="explanation-box">
                <strong>Why?</strong> {question.explanation}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Related Topics */}
      <div className="related-topics-section card">
        <h2>🔗 Related Topics for Further Reading</h2>
        <div className="topics-grid">
          {quizData.related_topics.map((topic, idx) => (
            <a
              key={idx}
              href={`https://en.wikipedia.org/wiki/${encodeURIComponent(topic)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="topic-chip"
            >
              {topic} →
            </a>
          ))}
        </div>
      </div>

      {/* Article Sections */}
      {quizData.sections?.length > 0 && (
        <div className="sections-section card">
          <h2>📑 Article Sections</h2>
          <div className="sections-list">
            {quizData.sections.map((section, idx) => (
              <button
                key={idx}
                className={`section-button ${activeSection === idx ? 'active' : ''}`}
                onClick={() => setActiveSection(activeSection === idx ? null : idx)}
              >
                {section}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default QuizDisplay;