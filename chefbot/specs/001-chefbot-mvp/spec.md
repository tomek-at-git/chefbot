# Feature Specification: ChefBot MVP — Chat With Your Recipe

**Feature Branch**: `001-chefbot-mvp`
**Created**: 2026-02-28
**Status**: Draft
**Input**: User description: "ChefBot is a chat-with-your-recipe solution, mobile app. The user should be able to ask questions about his recipe while he is cooking and has his hands occupied. E.g. 'What comes next after slicing the onion?', 'How much lemon juice if I only want to prepare the meal for 2 people?', 'What is a good replacement for Mirin?'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Ask a Step-by-Step Question (Priority: P1)

A cook is following a recipe and has just completed a step (e.g., slicing the onion). Their hands are messy or occupied. They ask ChefBot "What comes next?" and the system replies with the next step from the recipe, using short, clear language.

**Why this priority**: This is the core value proposition — hands-free, contextual guidance through a recipe. Without this, there is no product.

**Independent Test**: Load any recipe, advance to a middle step, and ask "What comes next?" — the system returns the correct next step in a concise, conversational sentence.

**Acceptance Scenarios**:

1. **Given** a recipe is loaded and the user is on step 3 of 8, **When** the user asks "What comes next?", **Then** the system responds with the instructions for step 4 in plain, concise language.
2. **Given** a recipe is loaded and the user is on the final step, **When** the user asks "What comes next?", **Then** the system responds that this is the last step and the dish is ready.
3. **Given** a recipe is loaded, **When** the user asks "What step am I on?", **Then** the system responds with the current step number and a brief summary.
4. **Given** no recipe has been loaded, **When** the user asks "What comes next?", **Then** the system prompts the user to select or provide a recipe first.

---

### User Story 2 — Adjust Quantities for Servings (Priority: P2) ⚠️ HEALTH-CRITICAL

A cook wants to prepare a recipe for a different number of people than the original recipe specifies. They ask something like "How much lemon juice if I only want to cook for 2?" and ChefBot recalculates the ingredient quantity based on the desired serving count.

**Why this priority**: Serving adjustment is one of the most frequently needed cooking calculations and a natural follow-up to step-by-step guidance.

**Health risk**: Incorrect quantities of certain ingredients (salt, sugar, spices, leavening agents, acidic liquids) can make food unsafe, inedible, or harmful — particularly for people with dietary restrictions such as diabetes or hypertension.

**Independent Test**: Load a recipe intended for 4 servings, ask "How much flour for 2 servings?" — the system returns the correctly scaled amount.

**Acceptance Scenarios**:

1. **Given** a recipe loaded with default 4 servings, **When** the user asks "How much lemon juice for 2 people?", **Then** the system responds with the correctly halved quantity and unit.
2. **Given** a recipe loaded with default 4 servings, **When** the user asks "Ingredients for 6 people?", **Then** the system lists all ingredients scaled to 6 servings.
3. **Given** the user asks to scale a recipe, **When** an ingredient has a non-divisible quantity (e.g., 1 egg for 4 servings, scaled to 3 servings), **Then** the system rounds to the nearest practical kitchen measurement and explains the rounding.
4. **Given** the quantity-scaling evaluation dataset, **When** the full dataset is run against the system, **Then** the system achieves ≥ 95% correctness on scaled quantities (exact match or within ±5% tolerance for continuous measures).

---

### User Story 3 — Suggest Ingredient Substitutions (Priority: P2) ⚠️ HEALTH-CRITICAL

A cook discovers they are missing an ingredient or wants to replace one for dietary reasons. They ask "What is a good replacement for Mirin?" and ChefBot suggests one or more alternatives, explaining how the substitution might affect the dish.

**Why this priority**: Elevated from P3 to P2 due to health implications. A wrong substitution can trigger allergic reactions (e.g., suggesting a tree-nut butter to replace dairy butter for someone who is allergic to nuts), cause adverse reactions for people with intolerances, or introduce unsafe ingredients. Substitutions prevent a cook from abandoning a recipe mid-preparation.

**Health risk**: Suggesting an allergen-containing substitute without a warning, or recommending an ingredient that is unsafe for a stated dietary restriction, can directly harm the user's health.

**Independent Test**: Load any recipe containing Mirin, ask "What can I use instead of Mirin?" — the system suggests at least one viable substitute with a brief explanation.

**Acceptance Scenarios**:

1. **Given** a recipe is loaded that contains Mirin, **When** the user asks "What is a good replacement for Mirin?", **Then** the system suggests at least one substitute with a brief note on flavour impact.
2. **Given** a recipe is loaded, **When** the user asks for a substitute for an ingredient that has no common replacement (e.g., a highly specialised spice), **Then** the system explains that no close substitute exists and suggests possible workarounds or skipping the ingredient.
3. **Given** a recipe is loaded, **When** the user asks to substitute an ingredient for dietary reasons (e.g., "I'm vegan, what can I use instead of butter?"), **Then** the system provides a dairy-free alternative and notes any texture or flavour differences.
4. **Given** the user states an allergy or dietary restriction (e.g., "I'm allergic to nuts"), **When** the system suggests a substitution, **Then** the suggested substitute MUST NOT contain the stated allergen, and the response MUST include a safety disclaimer reminding the user to verify ingredients.
5. **Given** the substitution evaluation dataset, **When** the full dataset is run against the system, **Then** the system achieves ≥ 90% relevance score on substitute suggestions AND 0% allergen-conflict rate (no substitute contradicts a stated allergy).
6. **Given** the user has dietary constraints saved in their profile, **When** the user asks for a substitution, **Then** the system applies both the saved profile constraints and any additionally stated constraints from the current conversation.

---

### User Story 4 — Build Health-Safety Evaluation Dataset (Priority: P1) ⚠️ HEALTH-CRITICAL

Before any health-critical feature (quantity scaling, substitutions) can be considered production-ready, a curated evaluation dataset MUST exist. This dataset serves as the automated regression gate that validates ChefBot does not give dangerous advice.

**Why this priority**: P1 because no health-critical feature may ship without passing its evaluation gate. The dataset is a prerequisite for Stories 2 and 3.

**Independent Test**: The dataset files exist, are version-controlled, and can be executed as an automated test suite that produces a pass/fail report with per-case scores.

**Acceptance Scenarios**:

1. **Given** the evaluation dataset is being created, **When** completed, **Then** it contains at least 50 quantity-scaling test cases covering whole numbers, fractions, non-divisible items (eggs), and edge multipliers (0.5×, 3×, 10×).
2. **Given** the evaluation dataset is being created, **When** completed, **Then** it contains at least 50 substitution test cases covering common allergens (gluten, dairy, nuts, shellfish, soy, eggs), dietary restrictions (vegan, vegetarian, halal, kosher), and general pantry swaps.
3. **Given** the substitution subset of the dataset, **When** reviewed, **Then** every test case that involves an allergy or dietary restriction explicitly encodes the expected constraint so that allergen-conflict detection can be scored automatically.
4. **Given** the substitution subset of the dataset, **When** each test case is created, **Then** a human curator labels the expected substitution(s) and relevance criteria so that automated runs can score against pre-labelled expected answers without requiring live human review.
5. **Given** the complete dataset, **When** run against the system, **Then** the test runner produces a structured report listing: overall pass rate, per-category pass rate, and every individual failure with input, expected output, and actual output.
6. **Given** the dataset, **When** a new model or prompt change is introduced, **Then** the evaluation suite MUST be re-run and results compared to the previous baseline before the change is merged.
7. **Given** the automated eval run flags cases where the system output does not match any pre-labelled expected answer, **When** a threshold of ambiguous/new cases is reached, **Then** those cases are queued for periodic human review and potential dataset expansion.

---

### User Story 5 — Load a Recipe Into the Conversation (Priority: P1)

Before a cook can ask questions, they need to provide ChefBot with a recipe. The user pastes or shares a recipe (plain text, URL, or photo) and ChefBot parses it, confirms the recipe name and serving count, and becomes ready for questions. If the user has dietary constraints saved in their profile, the system automatically checks the recipe's ingredients against those constraints and highlights any conflicts.

**Why this priority**: This is a prerequisite for all other stories — without a loaded recipe, no contextual questions can be answered. Tied P1 with Story 1.

**Independent Test**: Paste a recipe as plain text into the chat — the system confirms the recipe name, number of steps, and default serving count. If the user has a nut allergy in their profile and the recipe contains almonds, the system flags it.

**Acceptance Scenarios**:

1. **Given** the user has no recipe loaded, **When** the user pastes a recipe as plain text, **Then** the system parses the recipe, confirms the recipe name, number of steps, and default serving count.
2. **Given** the user has no recipe loaded, **When** the user sends a URL to a recipe page, **Then** the system fetches and parses the recipe and confirms the details.
3. **Given** a recipe is already loaded, **When** the user loads a new recipe, **Then** the system replaces the current recipe and confirms the switch.
4. **Given** the user pastes text that cannot be parsed as a recipe, **When** the system attempts to parse it, **Then** the system asks the user to clarify or provide the recipe in a supported format.
5. **Given** the user has dietary constraints saved in their profile, **When** a recipe is loaded, **Then** the system checks the recipe's ingredients against the user's constraints and highlights any conflicts (e.g., "⚠️ This recipe contains almonds — you have a tree nut allergy listed in your profile").
6. **Given** the user has no dietary constraints saved (or has disabled constraint checking), **When** a recipe is loaded, **Then** the system does not prompt about dietary constraints.

---

### User Story 6 — Set Up Dietary Profile (Priority: P2) ⚠️ HEALTH-CRITICAL

During first-time app setup, the user is optionally prompted to specify dietary constraints (allergies, intolerances, dietary preferences). These are persisted and used for automatic safety checks on recipe load and substitution suggestions. The user can update or disable constraint checking at any time via the app settings.

**Why this priority**: P2 because it directly supports the 0% allergen-conflict target (SC-007). While not required for basic recipe navigation (P1), it is a prerequisite for safe substitution and recipe-load warnings.

**Health risk**: If constraints are not captured or not applied, the system may suggest dangerous substitutions or fail to warn about allergens in a recipe.

**Independent Test**: Complete first-time setup specifying a nut allergy. Load a recipe containing walnuts — the system flags the conflict. Disable constraint checking in settings. Load the same recipe — no warning appears.

**Acceptance Scenarios**:

1. **Given** the user opens the app for the first time, **When** the onboarding flow is presented, **Then** the user is optionally asked to specify allergies and dietary restrictions from a predefined list (with a free-text option for unlisted items).
2. **Given** the user has completed onboarding without specifying constraints, **When** they later want to add constraints, **Then** they can do so from a settings screen at any time.
3. **Given** the user has specified constraints, **When** they want to update or remove them, **Then** they can do so from the settings screen and the changes take effect immediately for subsequent recipe loads.
4. **Given** the user has specified constraints, **When** they want to temporarily disable automatic constraint checking (e.g., cooking for guests with different needs), **Then** they can toggle an "Enable dietary checks" setting to off, and the system stops flagging conflicts until re-enabled.
5. **Given** the user has constraints saved and constraint checking enabled, **When** any recipe is loaded or any substitution is requested, **Then** the system applies the saved constraints without requiring the user to re-state them.

---

### Edge Cases

- What happens when the user asks a question that is unrelated to the recipe (e.g., "What's the weather?")?
  The system politely redirects the user to recipe-related topics.
- What happens when the user sends an extremely long recipe (e.g., 50+ steps)?
  The system processes it but warns the user that very long recipes may have reduced accuracy in step tracking.
- What happens when the user provides a URL that is paywalled, geo-blocked, times out, or cannot be parsed?
  The system informs the user why the URL couldn't be fetched (with a reason if known, e.g., "This page appears to require a login" or "The request timed out") and suggests pasting the recipe as plain text instead.
- How does the system handle multiple simultaneous recipe contexts (e.g., a main dish and a dessert)?
  MVP scope: only one recipe at a time. The system informs the user that loading a new recipe replaces the current one.
- What happens when the user asks about an ingredient not present in the loaded recipe?
  The system informs the user that the ingredient is not part of the current recipe and offers general cooking advice if applicable.
- What happens when the user provides quantities in a different unit system (metric vs. imperial)?
  The system responds using the same unit system as the original recipe. Unit conversion is out of MVP scope.
- What happens when the user disables dietary checks but then verbally mentions an allergy during conversation?
  The system still honours allergies stated explicitly in conversation, even if the profile-based checking is disabled. The toggle only controls automatic checks against the saved profile.
- What happens when the user mentions an allergy mid-conversation after already receiving a substitution?
  The system re-evaluates any prior suggestions in context and warns the user if a previously suggested substitute conflicts with the newly stated allergy.
- What happens when a substitution suggestion could be dangerous (e.g., raw kidney beans as a substitute)?
  The system MUST include a food-safety warning when a substitute requires special preparation to be safe.
- What happens when the system is uncertain about the safety of a substitution?
  The system MUST err on the side of caution — explicitly state the uncertainty and advise the user to consult a reliable source before proceeding.
- What happens when the LLM provider is unavailable or returns an error mid-conversation?
  The system retries once silently. If still failing, it shows a friendly message (e.g., "I'm having trouble thinking right now — please try again in a moment") and does not lose the current recipe or conversation context.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to load a recipe by pasting plain text into the chat.
- **FR-002**: System MUST allow users to load a recipe by providing a URL to a recipe webpage.
- **FR-003**: System MUST parse a loaded recipe into structured data: title, serving count, ingredient list (name, quantity, unit), and ordered steps.
- **FR-004**: System MUST maintain conversational context — tracking which recipe is loaded and which step the user is currently on.
- **FR-005**: System MUST answer step-by-step navigation questions (next step, previous step, current step, jump to step N).
- **FR-006**: System MUST recalculate ingredient quantities when the user requests a different serving count.
- **FR-007**: System MUST suggest ingredient substitutions when asked, with an explanation of how the substitute may affect the dish.
- **FR-008**: System MUST respond in concise, conversational language suitable for a hands-free cooking experience (short sentences, no walls of text).
- **FR-009**: System MUST handle ambiguous or incomplete user queries gracefully by asking a short clarifying question rather than guessing or failing silently.
- **FR-010**: System MUST support only one active recipe per conversation at a time (MVP scope).
- **FR-011**: System MUST inform the user when a requested ingredient is not part of the loaded recipe.
- **FR-012**: System MUST use the unit system present in the original recipe when responding (no automatic unit conversion in MVP).
- **FR-013**: System MUST redirect off-topic questions back to recipe-related assistance.
- **FR-014**: System MUST confirm recipe details (title, step count, serving count) upon successful recipe load.
- **FR-015**: System MUST provide a clear error message when recipe parsing fails and suggest corrective action. For URL-based loading, the error message SHOULD include the reason for failure if known (e.g., paywall, timeout, unsupported format) and MUST suggest pasting the recipe as text as a fallback.
- **FR-016**: System MUST NOT suggest an ingredient substitute that contradicts a user's stated allergy or dietary restriction within the same conversation.
- **FR-017**: System MUST include a brief safety disclaimer when providing substitution advice (e.g., "Always check labels for allergens").
- **FR-018**: System MUST flag uncertainty explicitly when it is not confident about the safety or suitability of a substitution, advising the user to verify independently.
- **FR-019**: All health-critical features (quantity scaling, substitutions) MUST pass automated evaluation against a dedicated evaluation dataset before release, with thresholds defined in the success criteria.
- **FR-020**: The evaluation dataset MUST be version-controlled, reviewable, and expanded over time as new edge cases are discovered.
- **FR-021**: System MUST respond to any user query within 5 seconds. Conversational queries (step navigation, substitutions, scaling) SHOULD respond within 2 seconds to maintain a natural dialogue flow during cooking.
- **FR-022**: When the LLM provider is unavailable or returns an error, the system MUST retry once silently. If the retry also fails, the system MUST display a user-friendly error message and MUST NOT lose the current recipe or conversation context.
- **FR-023**: System MUST allow users to optionally specify allergies and dietary restrictions during first-time app setup (onboarding).
- **FR-024**: System MUST persist the user's dietary constraints and apply them automatically when a recipe is loaded (checking ingredients against constraints) and when substitution suggestions are generated.
- **FR-025**: System MUST provide a settings screen where the user can add, update, or remove dietary constraints at any time, and toggle automatic dietary checking on or off.
- **FR-026**: When automatic dietary checking is disabled, the system MUST still honour allergies or restrictions explicitly stated by the user during the current conversation.

### Key Entities

- **Recipe**: The dish being prepared. Key attributes: title, default serving count, source (text or URL), list of ingredients, ordered list of steps.
- **Ingredient**: A single item used in a recipe. Key attributes: name, quantity, unit. Belongs to exactly one recipe.
- **Step**: An ordered instruction within a recipe. Key attributes: step number, instruction text. Belongs to exactly one recipe.
- **Conversation Context**: The runtime state of a user's session. Key attributes: loaded recipe, current step index, requested serving count (if different from default), in-conversation stated allergies and dietary restrictions (supplements profile constraints).
- **User Profile**: Persistent user preferences stored on the device. Key attributes: dietary constraints (list of allergies, intolerances, dietary preferences), dietary-check-enabled flag. Created during onboarding, editable via settings.
- **Evaluation Dataset**: A curated, version-controlled set of test cases used to validate health-critical features. Key attributes: test case ID, category (scaling / substitution / allergen-safety), input (recipe + user query), expected output, pass/fail criteria.

## Clarifications

### Session 2026-02-28

- Q: How should ChefBot behave when the LLM provider is unavailable or returns an error mid-conversation? → A: Retry once silently; if still failing, inform the user with a friendly message and suggest retrying in a moment.
- Q: Should ChefBot proactively ask about allergies, or only capture them when mentioned? → A: Dietary constraints are specified once during first-time app setup (optional), persisted in a user profile, and automatically checked against each loaded recipe. The behaviour is configurable in the UI so users without constraints are not prompted on every recipe.
- Q: How should "human review" work for substitution relevance scoring in the evaluation dataset? → A: Expected outputs are human-curated at dataset creation time. Automated eval runs compare system output against pre-labelled expected answers. New or ambiguous cases are flagged for periodic human review.
- Q: How should the system handle unfetchable recipe URLs (paywalled, geo-blocked, timeout)? → A: Inform the user the URL couldn't be fetched (with reason if known: paywall, timeout, unsupported format) and suggest pasting the recipe as text instead. Image/photo upload of recipes is a desired future capability but out of MVP scope.

## Assumptions

- The user interacts with ChefBot through a text-based chat interface (voice input/output via the mobile device's built-in speech-to-text and text-to-speech capabilities is handled at the OS/device level, not by ChefBot itself in the MVP).
- Recipe URLs will point to common recipe websites that use structured data (e.g., schema.org Recipe markup) or have well-known HTML structures. Exotic or paywalled sites may not be supported.
- The LLM handles natural language understanding and response generation; the application orchestrates recipe state (current step, serving multiplier) around the LLM.
- No user accounts or persistent storage of recipes across sessions in the MVP. Each conversation starts fresh. However, lightweight local persistence IS required for the user's dietary profile (allergies, dietary restrictions, preferences) — this is stored on-device and does not require server-side accounts or authentication.
- No image-based recipe input (photo of a cookbook page) in the MVP. This is a desired future capability and a strong candidate for a subsequent iteration (e.g., `002-image-recipe-upload`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can load a recipe and receive confirmation within 5 seconds of submitting it.
- **SC-002**: Users receive a contextually correct answer to a step navigation question within 2 seconds.
- **SC-003**: ≥ 95% of serving adjustment calculations in the evaluation dataset return a correctly scaled quantity (exact match or within ±5% tolerance for continuous measures). ⚠️ HEALTH-CRITICAL
- **SC-004**: Users can complete a full recipe walkthrough (load recipe → navigate all steps → finish) in a single uninterrupted conversation.
- **SC-005**: ≥ 90% of substitution suggestions in the evaluation dataset match a human-curated expected answer (pre-labelled at dataset creation time). ⚠️ HEALTH-CRITICAL
- **SC-006**: 95% of parsed recipes correctly identify the title, serving count, and all ingredients and steps.
- **SC-007**: 0% allergen-conflict rate — no substitution in the evaluation dataset suggests an ingredient that contradicts the user's stated allergy or dietary restriction. ⚠️ HEALTH-CRITICAL
- **SC-008**: The evaluation dataset contains ≥ 100 test cases (≥ 50 quantity-scaling, ≥ 50 substitution including allergen scenarios) and is executed as part of the automated test suite.
- **SC-009**: Every model or prompt change MUST demonstrate no regression on the evaluation dataset (scores equal to or better than the previous baseline) before merging.
