import './SplashScreen.css';

export const SplashScreen = ({ onStart }: { onStart: () => void }) => (
  <div className="splash">
    <h1 className="splash-title">doggo blocks</h1>
    <img src="doggo-blocks-sparkle.png" alt="doggo blocks" className="splash-image" />
    <button className="splash-btn" onClick={onStart}>
      Start Coding
    </button>
  </div>
);
