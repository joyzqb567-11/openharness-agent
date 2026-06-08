# Phase90 Live App Dispatcher Design

## Objective

Build the first controlled live app dispatcher for Windows Computer Use. It should route an authorized representative app action through the real production safety stack without enabling uncontrolled desktop control by default.

## Architecture

Phase90 composes existing proven layers instead of replacing them:

- Phase60 persistent grants decide whether a representative app action is authorized.
- Phase69 app/window control provides a stable app launch and focus identity.
- Phase71 generic input actions provide reusable input event shapes.
- Phase72 real app safety boundary blocks dangerous windows, missing grants, bypass attempts, and aborts.
- Phase74 representative matrix provides Paint Pikachu stroke evidence.
- Phase58 remains the optional safe-window real SendInput smoke path.

## Success Criteria

- Authorized Notepad action reaches the dispatcher event layer.
- Unauthorized representative app action produces zero low-level events.
- Dangerous target such as PowerShell produces zero low-level events.
- Text payloads are logged only by length and digest.
- Paint Pikachu remains a humanlike stroke plan with no direct image-file cheat.
- Default real dispatch remains disabled.
- Real visible terminal acceptance passes through `start_oauth_agent.bat`.

## Safety Boundary

Phase90 is not a promise of perfect arbitrary-app control. It creates a controlled dispatch path. Real dispatch still requires explicit environment gates, persistent grants, target identity checks, abort checks, cleanup, and visible terminal acceptance.
