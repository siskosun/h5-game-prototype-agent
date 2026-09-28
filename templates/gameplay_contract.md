# Gameplay Contract

## 1. Player Promise and Scope

## 2. Core Loop

## 3. State and Legal Actions

Describe P0 mechanics with Trigger -> Preconditions -> Player Action -> State Delta -> Feedback -> Termination.

## 4. Mechanics and Numeric Envelope

### Meaningful-Choice Audit

Use explicit N/A when no recurring multi-option decision exists.

## 5. Screens, Input, and Feedback

## 6. Mechanic Curriculum

Use explicit N/A for a single-scenario prototype.

## 7. Persistence

Use `Persistence: none` when no save is required. Otherwise define schema version and run/meta ownership.

## 8. Headless Simulation Contract

Map the production core functions/actions used by Node simulation. Include `render_game_to_text`, `advanceTime`, and `__GAME_API__` browser hooks.

## 9. Acceptance Tests

Use deterministic Given / When / Then cases for each P0 rule.

## 10. Out of Scope
