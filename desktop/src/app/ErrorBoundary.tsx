/**
 * The last line of defence for the window.
 *
 * Without it, one view throwing while it renders unmounts everything and
 * leaves a blank window with no way back. The session itself lives in the
 * daemon and its checkpoint, so reloading the window loses nothing that was
 * saved; the message says what failed so it can be reported.
 */
import { Component, ErrorInfo, ReactNode } from "react";

type State = { error: Error | null };

export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("NetZoo window error", error, info.componentStack);
  }

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;
    return (
      <div className="startup startup--failed" role="alert">
        <div className="startup__card">
          <p className="startup__title">This view stopped working</p>
          <p>The window hit an error it could not recover from. Your sessions are saved; reloading the window brings them back.</p>
          <pre className="fv__text">{error.message || String(error)}</pre>
          <button className="btn btn--primary" type="button" onClick={() => window.location.reload()}>Reload the window</button>
        </div>
      </div>
    );
  }
}
