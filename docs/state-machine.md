# State Machine and Domain Invariants (v1.0)

## Lifecycle states

### ProductHypothesis
- `product_discovery`
- `site_ready`
- `traffic_running`
- `traffic_completed`
- `finalized`

### LandingPage
- `draft`
- `ready_for_traffic`

### TrafficTest
- `planned`
- `running`
- `completed`

### FinalDecision
- `recorded`

## Allowed transitions
1. `product_discovery -> site_ready`
   - requires landing page `mobile_ready=1`
2. `site_ready -> traffic_running`
   - requires landing page `ready_for_traffic`
3. `traffic_running -> traffic_completed`
   - requires traffic test `running`
4. `traffic_completed -> finalized`
   - requires completed traffic test
   - requires no existing final decision
   - requires consistent `final_outcome == postmortem.next_action`

## Forbidden transitions (enforced)
- нельзя переводить hypothesis в `site_ready` без готового landing
- нельзя стартовать traffic test, если hypothesis не `site_ready`
- нельзя финализировать hypothesis без `traffic_completed`
- нельзя финализировать hypothesis дважды
- нельзя иметь несогласованный final outcome vs next action

## Where enforced
- `app/services/state_machine.py`
- `app/services/finalization.py`
- `app/services/workflow.py` (demo-cycle follows valid path)
