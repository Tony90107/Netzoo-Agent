# NetZoo input identification manual tests

This fixture is designed for PANDA input discovery.

## Test 1: random filenames, valid content

Directory: `random_names_valid/`

Expected behavior:

- The files should be mapped from their contents, not their filenames.
- The plan should show `needs_confirmation`.
- No PANDA tool should run before confirmation.
- After answering yes, the inputs should be re-planned and validated.

The prompt intentionally does not name or describe the expected roles. The agent
must discover them from the files itself.

## Test 2: plausible filenames, invalid content

Directory: `correct_names_invalid_content/`

Expected behavior:

- The filename hints should not be trusted by themselves.
- PANDA preflight should report an invalid motif input.
- The plan should remain `needs_input`; it must not become `ready`.

The prompt intentionally does not mention that the content is invalid. The agent
must discover and report the problem itself.

Use the two prompt files in this directory as the user messages.
