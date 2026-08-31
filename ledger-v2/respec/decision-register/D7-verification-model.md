# D7: Verification, calibrated taste judges
Date: 2026-08-31. Status: APPROVED.
Context: authored breadth is bounded by the scarcest verifier, Jafar's eyes. The fix is to turn taste into an instrument.
Choice: for each content type with a taste dimension (frames, dialogue tone, brand bible pieces, faces), Jafar grades a calibration sample of 30 to 50 items pass/fail with one-line reasons. A judge (vision or text model) is tuned until agreement with Jafar is at or above 80 percent on a held-out set, with zero false passes on canon violations. Only then does the judge verify at scale; Jafar audits a 10 percent sample ongoing. Recalibrate when the content type shifts, when audit disagreement exceeds 20 percent, or on any canon-violation false pass.
Consequence: Jafar's feel-check bandwidth stops being the breadth ceiling; measured agreement replaces vibes.
