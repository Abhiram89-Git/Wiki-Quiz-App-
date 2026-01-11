import React, { useState } from 'react';

function QuizMode({ quizData }) {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);

  const quiz = quizData.quiz;
  const question = quiz[currentQuestion];

  const handleAnswerSelect = (option) => {
    setUserAnswers({
      ...userAnswers,
      [currentQuestion]: option,
    });
  };

  const handleNext = () => {
    if (currentQuestion < quiz.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      setShowResults(true);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const calculateScore = () => {
    let correct = 0;
    quiz.forEach((q, idx) => {
      if (userAnswers[idx] === q.answer) {
        correct++;
      }
    });
    return { correct, total: quiz.length, percentage: Math.round((correct / quiz.length) * 100) };
  };

  if (showResults) {
    const score = calculateScore();
    const scoreColor = score.percentage >= 70 ? '#4CAF50' : score.percentage >= 50 ? '#FFC107' : '#F44336';

    return (
      <div className="quiz-results-modal">
        <div className="results-card">
          <h2>📊 Quiz Results</h2>
          
          <div className="score-circle">
            <div className="score-display" style={{ color: scoreColor }}>
              <span className="score-number">{score.percentage}%</span>
              <span className="score-label">Score</span>
            </div>
          </div>

          <div className="score-details">
            <p className="score-text">
              You got <strong>{score.correct} out of {score.total}</strong> questions correct!
            </p>
            {score.percentage >= 70 && <p className="feedback excellent">Excellent! 🎉</p>}
            {score.percentage >= 50 && score.percentage < 70 && <p className="feedback good">Good effort! 👍</p>}
            {score.percentage < 50 && <p className="feedback needwork">Keep learning! 📚</p>}
          </div>

          <div className="results-breakdown">
            <h3>Question Breakdown</h3>
            {quiz.map((q, idx) => {
              const userAnswer = userAnswers[idx];
              const isCorrect = userAnswer === q.answer;
              return (
                <div key={idx} className={`result-item ${isCorrect ? 'correct' : 'incorrect'}`}>
                  <span className="result-number">Q{idx + 1}</span>
                  <div className="result-content">
                    <p className="result-question">{q.question}</p>
                    <p className="result-answer">
                      Your answer: <strong>{userAnswer || 'Not answered'}</strong>
                      {!isCorrect && (
                        <span> → Correct: <strong>{q.answer}</strong></span>
                      )}
                    </p>
                  </div>
                  <span className={`result-icon ${isCorrect ? 'correct' : 'incorrect'}`}>
                    {isCorrect ? '✓' : '✗'}
                  </span>
                </div>
              );
            })}
          </div>

          <button
            onClick={() => {
              setCurrentQuestion(0);
              setUserAnswers({});
              setShowResults(false);
            }}
            className="button button-primary"
          >
            Retake Quiz
          </button>
        </div>
      </div>
    );
  }

  const isAnswered = userAnswers[currentQuestion] !== undefined;

  return (
    <div className="quiz-mode">
      <div className="quiz-progress">
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${((currentQuestion + 1) / quiz.length) * 100}%` }}
          />
        </div>
        <p className="progress-text">
          Question {currentQuestion + 1} of {quiz.length}
        </p>
      </div>

      <div className="quiz-card">
        <div className="quiz-card-header">
          <h2>{question.question}</h2>
          <span className="difficulty-badge" style={{
            backgroundColor: {
              easy: '#4CAF50',
              medium: '#FFC107',
              hard: '#F44336',
            }[question.difficulty]
          }}>
            {question.difficulty}
          </span>
        </div>

        <div className="options-container">
          {question.options.map((option, idx) => {
            const letter = String.fromCharCode(65 + idx);
            const isSelected = userAnswers[currentQuestion] === option;

            return (
              <button
                key={idx}
                onClick={() => handleAnswerSelect(option)}
                className={`option-button ${isSelected ? 'selected' : ''}`}
              >
                <span className="option-letter">{letter}</span>
                <span className="option-content">{option}</span>
              </button>
            );
          })}
        </div>

        <div className="quiz-navigation">
          <button
            onClick={handlePrevious}
            disabled={currentQuestion === 0}
            className="button button-secondary"
          >
            ← Previous
          </button>

          <button
            onClick={handleNext}
            disabled={!isAnswered}
            className="button button-primary"
          >
            {currentQuestion === quiz.length - 1 ? 'Submit Quiz' : 'Next →'}
          </button>
        </div>

        <div className="question-indicators">
          {quiz.map((_, idx) => (
            <div
              key={idx}
              className={`indicator ${
                idx === currentQuestion
                  ? 'current'
                  : userAnswers[idx]
                  ? 'answered'
                  : 'unanswered'
              }`}
              onClick={() => setCurrentQuestion(idx)}
            >
              {idx + 1}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default QuizMode;