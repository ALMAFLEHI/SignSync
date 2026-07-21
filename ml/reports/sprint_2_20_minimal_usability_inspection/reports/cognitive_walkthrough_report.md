# Sprint 2.20 Cognitive Walkthrough

Evaluator: one developer/researcher. Observations: 64; all are researcher observations, not participant reactions.

## Home

- **CW01 PASS:** Start Banking Interaction is a prominent labelled primary action.
- **CW02 PASS:** The label describes the task in banking language.
- **CW03 PASS:** Navigation opens the dedicated banking interaction screen.
- **CW04 PASS:** The user remains on Home until the action is selected.
- **CW05 PASS:** The primary start action is visible in the normal flow.
- **CW06 PASS:** Offline processing and No video upload are visible on Home.
- **CW07 PASS:** Developer tools are absent from the normal Home flow.
- **CW08 PASS:** The heading and short workflow guidance use plain language.

## Recognition

- **CW01 PASS:** The capture action and banking-only context are labelled.
- **CW02 PASS:** The screen asks for a banking sign rather than a model input.
- **CW03 PASS:** Capture progress and recognition outcome are surfaced.
- **CW04 PASS:** Cancel and retry paths return to a clean state.
- **CW05 PASS:** A successful result advances to intent confirmation.
- **CW06 PASS:** The surrounding workflow states that processing is offline.
- **CW07 PASS:** Normal recognition does not expose developer diagnostics.
- **CW08 PASS:** User-facing instructions avoid feature-vector terminology.

## Intent confirmation

- **CW01 PASS:** Confirm Intent, Try Again, and Cancel Interaction are visible.
- **CW02 PASS:** Each action uses a direct verb and a human-readable topic.
- **CW03 PASS:** The detected topic and confidence provide immediate status.
- **CW04 PASS:** Try Again clears the prediction; Cancel clears and exits.
- **CW05 PASS:** Confirm Intent clearly advances to related requests.
- **CW06 PASS:** No entered customer details exist at this step.
- **CW07 PASS:** The intent is displayed as Account, Transfer, and similar wording.
- **CW08 PASS:** The confirmation question explains why confirmation is needed.

## Query selection

- **CW01 PASS:** Four selectable requests and labelled navigation actions are visible.
- **CW02 PASS:** Requests are full customer sentences rather than internal IDs.
- **CW03 PASS:** Selection state is visible and enables Continue.
- **CW04 PASS:** Back and Cancel Interaction are available.
- **CW05 PASS:** Continue is visible but disabled until a request is selected.
- **CW06 PASS:** No manual customer details are requested on this page.
- **CW07 PASS:** Query IDs remain hidden from the user.
- **CW08 PASS:** The confirmed topic and four related requests provide context.

## Manual details

- **CW01 PASS:** Optional fields and Review Request are labelled.
- **CW02 PASS:** Labels describe banking details such as amount and account number.
- **CW03 PASS:** Validation errors and masked input state are displayed in context.
- **CW04 PASS:** Back and Cancel are available; fields can be corrected.
- **CW05 PASS:** Review Request is the prominent next action.
- **CW06 PASS:** The page states that information remains in this session.
- **CW07 PASS:** Raw field IDs and storage implementation are hidden.
- **CW08 PASS:** Optional wording and familiar field labels are explicit.

## Request review

- **CW01 PASS:** Show to Banker, Edit Request, Edit Details, and Start Over are labelled.
- **CW02 PASS:** The page summarizes the banking topic and selected request.
- **CW03 PASS:** Masked populated details are shown before banker handoff.
- **CW04 PASS:** Edit and Start Over actions support correction or reset.
- **CW05 PASS:** Show to Banker is the primary action.
- **CW06 PASS:** Sensitive values remain masked and empty optional fields are omitted.
- **CW07 PASS:** Internal intent, query, and field IDs are absent.
- **CW08 PASS:** The review uses customer-readable labels and values.

## Banker view

- **CW01 PASS:** New Interaction, Back to Review, and Clear Session are labelled.
- **CW02 PASS:** The handoff is titled Customer Banking Request.
- **CW03 PASS:** Topic, request, and populated details are clearly summarized.
- **CW04 PASS:** The banker can return, start a new interaction, or clear the session.
- **CW05 PASS:** New Interaction is prominent after the request is read.
- **CW06 PASS:** Offline processing and Session only are visible.
- **CW07 PASS:** Confidence, TFLite, and internal IDs are not displayed.
- **CW08 PASS:** The bank-staff disclaimer states that SignSync takes no action.

## Reset and recovery

- **CW01 PASS:** Try Again, Cancel, Start Over, New Interaction, and Clear Session exist.
- **CW02 PASS:** Reset actions use familiar, explicit labels.
- **CW03 PASS:** The workflow returns to recognition with no prior values.
- **CW04 PASS:** Every main stage has a safe back, retry, cancel, or reset path.
- **CW05 PASS:** A clean recognition screen is shown after reset.
- **CW06 PASS:** Reset clears temporary manual values from the controller.
- **CW07 PASS:** State cleanup occurs without exposing implementation details.
- **CW08 PASS:** Automated scenarios verify that old values do not return.

This sprint used a formative researcher-led usability inspection and automated workflow validation. No external participants were available. The findings identify interface strengths and potential improvements but cannot replace future evaluation with Deaf and hard-of-hearing users, banking staff, and independent participants.
