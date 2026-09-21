/**
 * The Plan pane: a scroll container that resets when the plan changes.
 *
 * A plan can be much taller than the pane, and the previous one's scroll
 * position is meaningless for the next one — leaving it where it was hid the
 * workflow name and the evidence ledger behind a scrollbar the moment a
 * second plan arrived.
 */
import { useEffect, useRef } from "react";

import { WorkflowPlan } from "../../transport/protocol";
import { PlanCard } from "./PlanCard";

export function PlanPane({
  plan,
  hash,
}: {
  plan: WorkflowPlan | null;
  hash: string | null;
}) {
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Assigning scrollTop rather than calling scrollTo: it is the one form
    // every environment implements, jsdom included.
    if (scroller.current) scroller.current.scrollTop = 0;
  }, [hash]);

  return (
    <section className="pane">
      <header className="pane__header">Plan</header>
      {plan ? (
        <div className="pane__scroll" ref={scroller} data-testid="plan-scroll">
          <PlanCard plan={plan} hash={hash} />
        </div>
      ) : (
        <div className="pane__empty">No plan yet. Describe a goal to get one.</div>
      )}
    </section>
  );
}
