# Tool visibility fix

## Goal

Ensure existing conversations display tool parameters and responses clearly so users can audit tool usage without rerunning prompts.

## Tasks

- [ ] Inspect current ToolInteraction styles against the dark theme to confirm why text appears invisible.
- [ ] Update ToolInteraction styling (colors, typography, layout) so parameters and responses remain readable in both light and dark blocks.
- [ ] Validate in the running UI and clean up any temporary debugging aids.

## Decisions & Notes

- ToolInteraction now sets explicit dark text colors, box shadow, and wrapping to keep parameters/results readable against the dark theme containers.
- Removed temporary console logging from ChatWindow after verifying metadata flow.
