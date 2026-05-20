import './SplashScreen.css';

export const SplashScreen = ({ onStart }: { onStart: () => void }) => (
  <div className="splash">
    <h1 className="splash-title">doggo code blocks</h1>
    <img src="doggo-code-blocks-sparkle.png" alt="doggo code blocks" className="splash-image" />
    <button className="splash-btn" onClick={onStart}>
      Start Coding
    </button>
  </div>
);
