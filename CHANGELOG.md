# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- Markdownlint-disable MD024 -->

## [Unreleased]

### Changed

- Updated multiple dependencies to their latest versions, ensuring compatibility with upstream improvements and maintaining project stability without introducing breaking changes;... [5da4f2a8](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/5da4f2a8922f53ff090e81f06f1dc22bfc9e35db)
- Streamlined maintenance and reduced risks by introducing concurrency control to prevent overlapping dependency updates and standardizing version update automation messages. [48baa307](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/48baa30765b8ecf6cebe5bc7d6974c7d0bfd1f60)
- Improved maintainability and reduced the likelihood of errors by enabling fine-grained control over auto-updating GitHub Actions through explicit lists for exceptions and pinned... [71ed1bdb](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/71ed1bdb34a6184e23a0f1749f42d1d05b691e36)

## [6.2.0] - 2026-08-04

### Added

- Warns users of oversized diffs that would trigger unclear errors or empty commit messages by skipping LLM requests and returning a clear warning message if the estimated token c... [89dd13f9](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/89dd13f9fd30910403b478521074767673a19bee)

### Changed

- Enabled suppression of line-length warnings from YAMLlint in GitHub Actions workflow files and default commit message prompt YAML to reduce noise in linting results for long ref... [8adbb901](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/8adbb9015eacfbb165d41a51c88ee897230fffb8)

## [6.1.1] - 2026-07-24

### Added

- Enabled better spell checking for documentation and code comments by introducing 'nav', 'walkthrough', and 'walkthroughs' to the wordlist used across the project. [d24b7bed](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/d24b7bed8136a6695ba20c3a1297b039038562b4)

### Changed

- Optimized documentation layout and content for improved user navigation and clarity by separating conceptual explanations, task-based guides, reference material, and tutorials,... [543c78b1](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/543c78b1c5339e9c591eea6a8b78a1e611e6297f)
- Upgraded aiohttp to version 3.14.1 and added headroom-ai as dependencies in the project's `uv.lock` file, potentially requiring users with customized dependencies to take migrat... [36b90605](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/36b906055bc054b4f0e7e7488781fcd786ca37aa)
- Updated dependencies to versions aiohttp 3.14.3, annotated-types 0.8.0, and anyio 4.14.2 from previous versions 3.14.1, 0.7.0, and 4.14.0 respectively. [d36dbc3b](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/d36dbc3bafadd8d89522b3f6cb5bc26277a5687a)
- Simplified internal test structure and callback configuration to improve maintainability and readability without altering functional behavior. [21a72d69](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/21a72d69d09b010e524eff68b54295a379523ff8)

### Removed

- Simplified the conditional check for an empty commit_hash variable to accurately handle whitespace and unset values in ci scripts. [a1f542af](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/a1f542afe2270a2225147651f01e15fe916b56b8)

## [6.1.0] - 2026-06-18

### Added

- Clarified the expected formatting for commit message bodies by explicitly guiding AI-generated messages to use semantic line breaks and ensuring each sentence appears on its own... [2f9edb3f](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/2f9edb3fdb1163c036f0e100e4f136fcc4071a44)
- Enabled robustness in LLM interactions by introducing retry logic and integrating Headroom prompt compression to handle intermittent empty results and support prompt compression... [52e93b8e](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/52e93b8ece6f917eca6e84080aa86dccb55a3a8f)

## [6.0.0] - 2026-06-05

### Added

- BREAKING: Modernized commit message prompts to include "revert" and "style" types and refined formatting guidelines, requiring updates to existing validation logic due to the breaking cha... [53b94c6f](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/53b94c6f6578c4b4eae4ec685922c671381d639d)

## [5.1.1] - 2026-06-05

### Changed

- Updated dependencies to include aiohttp version 3.13.5 and black version 26.5.0, without introducing any breaking behavior, migration requirements, or changes to the API contrac... [d284aab0](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/d284aab0b452c7f83ca64601f90ba8357f572f76)
- Mypy lint runs are now more resilient to missing PyYAML type stubs, continuing without errors due to the improved handling of untyped imports. [63044b79](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/63044b7965322724c291fa7f24fea3c18bd44499)
- Upgraded aiohttp dependency to version 3.14.0 to remediate Trivy-reported CVEs and ensure security compliance for users and maintainers who may need to update their existing cod... [9eaf6485](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/9eaf64854f25b130d5cbf261e9b3d52b5603fd92)

### Fixed

- Resolved transient network errors in production by increasing the default maximum attempts for retrying from 3 to 5, aligning with observed failure rates and reducing false-posi... [6017f17b](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/6017f17bdf75bda958ea9ad99dec12f866a211e1)

### Removed

- Simplified the readme by eliminating redundant documentation about project documentation location which was already stated elsewhere. [164e9f32](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/164e9f32c65e3dddc5f2c6ce4e52f19f251574f3)

## [5.1.0] - 2026-05-17

### Added

- Enforced stricter Conventional Commits syntax for automated commit messages including mandatory lowercase type and scope, correct punctuation, and adherence to commitlint valida... [be13b69b](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/be13b69be39dac83d2b1849ff98612fa222fcddf)
- Enabled clear and consistent application of semantic line breaks in Markdown files by specifying guidelines for sentence and clause boundaries while preserving rendered output a... [84a88415](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/84a88415530917de490617896ffd15b3b4f3845d)
- Enforced strict testing requirements for Python code changes to ensure high-quality code and consistent development practices by mandating the execution of `make test` after mod... [4967f5f0](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/4967f5f032fcc18032e8537e5eb41ebc8d23b4db)
- Introduced project quality gates for contributors by enforcing linting and formatting checks on every file modification through the `make lint` and `make fmt` commands, requiring t... [77063f6d](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/77063f6d1bf9753cf3a4d1eb2ee4bb4cf3f940cf)
- Unlocked interactive confirmation for generated commit messages, prompting users to accept the message before writing it unless the --auto-approve flag is set or the AI_PREPARE_C... [f233a154](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/f233a1542afcfe05e9a8b64fcdde4b532485607b)

### Changed

- Clarified and modernized the AI-powered Git hook's commit-message generation prompt to conform to OpenStack's best practices and Conventional Commits format, resulting in more i... [ff92e528](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/ff92e52823533d4f5b61f5fb8b935b66c32666fa)
- Upgraded pre-commit configuration to leverage the maintained Markdownlint-cli Node.js CLI version for improved compatibility and ongoing support. [18996f52](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/18996f52f55a352b9d3344d4f1dedb6966e65483)
- Simplified the documentation structure to improve user experience and maintainability by providing clear entry points for learning, doing, and reference. [57091f79](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/57091f7969ffd27d5260ee3524391a52322af940)
- Stabilized Python coding standards by introducing a comprehensive guidelines document that consolidates and expands upon previous requirements, emphasizing tool usage like black... [6ad20eab](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/6ad20eab4265722b3db9eab0d584d084d1c008be)
- Modernized type hints and improved path handling by replacing legacy typing constructs with built-in generics and pathlib.Path instances. [7a0757ec](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/7a0757ec42395f654c812258a7d942367ed7eb32)
- Updated the wordlist to include new terms and reorder existing ones for consistency, preventing false positives in spelling and linting checks. [6f54e1a8](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/6f54e1a8fb4f697524aa6c02118ed9bfe687b600)

### Removed

- Simplified repository configuration by removing obsolete instructions for GitHub Copilot and SemBr prompts from the repository's Markdown files, reducing maintenance overhead an... [762f9b47](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/762f9b47fa6d007e387078504152ec24adda7ada)
- Streamlined formatting by eliminating reliance on pyink and instead relying on black, isort, and ruff to reduce redundancy and potential conflicts between formatters. [ec089db4](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/ec089db412e5acd360a2da0c6246755d1023a618)

## [5.0.3] - 2026-05-08

### Fixed

- Hardened token authentication by introducing WORKFLOW_TOKEN as an environment variable and updating GitPython to version 3.1.50 to resolve security vulnerabilities. [57ffd140](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/57ffd1405924df2aa264e5930881c26a87461be7)

## [5.0.2] - 2026-05-08

### Changed

- Standardized GitHub Actions workflows across lint, spell check, and update workflows to ensure consistency in pinned versions while preserving repository-specific behavior. [de95b380](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/de95b380b86dba1b926b301b44782e44acca126f)
- resolved CVE-2026-28684 by upgrading python-dotenv to >=1.1.0, thereby improving security for users of this library without requiring any migration steps or affecting API or CLI... [0dd22039](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/0dd22039e00b2d626d73a752f5aad511e38b4ed2)

### Fixed

- Resolved four security vulnerabilities by upgrading GitPython to version 3.1.50 and adding the versions-update environment variable to the check-versions job in the workflow fil... [1b2c93a9](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/1b2c93a903e64c73485486b0abf51144f6aff2bd)

## [5.0.1] - 2026-04-11

### Changed

- Updated dependencies to include aiohttp 3.13.5, anyio 4.13.0, attrs 26.1.0, and keep beautifulsoup4 at 4.14.3, with potential migration steps required for the upgraded aiohttp v... [8427073b](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/8427073bce746c63560ead82a1cd27a0d34b420e)

### Fixed

- The format of the copilot-instructions.md file was stabilized to adhere to Markdownlint and prettier guidelines by converting multiple H1 headings to H2 and correcting make test... [86f73a73](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/86f73a73593d9dae19d23c37cb4d7bf8210d44c0)

## [5.0.0] - 2026-04-02

### Added

- BREAKING: Enabled fine-grained control over logging verbosity by introducing a --log-level option that replaces the --verbose flag, requiring users to update their pre-commit configs and... [b39ae713](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/b39ae7133afd8011f2568a0192c47246d6f67458)

## [4.3.0] - 2026-04-02

### Added

- Enabled configuration of GitHub model information through environment variables, allowing users to set necessary API keys and ensure proper setup for models like GitHub Copilot... [b02506a2](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/b02506a2c57e723eb7123f295eaea2cfa9e5356f)

## [4.2.0] - 2026-04-02

### Added

- Enabled GitHub Copilot to follow custom instructions for generating code in the repository by adding new requirements for code formatting, testing, and documentation without int... [05076ec3](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/05076ec3b7f3a7cc030b1bb589f313fa3c8871f7)

## [4.1.0] - 2026-04-02

### Added

- Enabled improved reliability in generating commit messages by introducing a timeout mechanism that allows for fallbacks when the model takes too long to respond and requires set... [ad1b281c](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/ad1b281cdcffc15c960669a6c5f1c5d5cd4e47e9)

### Changed

- Enabled GitHub Actions workflows to utilize latest versions of various actions including Markdown link checking and super-linter validation while introducing AI analysis for fai... [4b0f4dc0](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/4b0f4dc00f617e84300a173c5f31a258d151950f)
- Updated GitHub Actions workflows to utilize version 6.0.1 of the actions/checkout action, requiring migration steps for users who customized their workflows with specific versio... [b290ac40](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/b290ac40527a04280263d8967c36743a290a1010)
- Refined versions files to reflect the latest dependencies for uv, aiohttp, and other packages available on PyPI, which may require users relying on these dependencies to migrate... [a734128e](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/a734128efe0cda973fdfe1c689cf3872ec666702)
- Upgraded project dependencies to versions 0.14.9 for ruff and 2.6.2 for urllib3. [57fd05f5](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/57fd05f556172ea9e380e404c3fa76ce5f492f0a)
- Modernized versions files to leverage the latest packages, including aiohttp, aiosignal, annotated-types, anyio, attrs, beautifulsoup4, and black, potentially requiring users wi... [3daa7bfd](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/3daa7bfddb8023c82528bb786ee2be3b6d34cef3)
- Optimized dependencies to resolve zizmor CI pipeline issues by replacing an archived action with a native Git diff step and fixing template injection in the Get diff step, also up... [d0137355](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/d0137355f835bb4a1fd1d18a77106c97e93e2a09)

## [4.0.0] - 2025-12-05

### Added

- BREAKING: Enabled explicit pre-commit validation disabling by adding the `VALIDATE_PRE_COMMIT` option to environment variables, making it clear that this feature is intentionally disabled... [88bc3cb5](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/88bc3cb5dbcdf6431558341626181f983e68ed49)

## [3.1.0] - 2025-12-05

### Added

- Enabled developers to generate completions that align with the LLaMA APIs requirements by updating the `completion` method in the `DummyLite` class to include parameters for te... [a77787c4](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/a77787c481f8e1416ebc0c3e10861428ada0052f)

## [3.0.0] - 2025-12-05

### Added

- Enabled project-wide coding style consistency by introducing an .editorconfig file that enforces indentation of 4 spaces for shell scripts and the tox environment while ignoring... [21ceed33](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/21ceed330843536c93e83160adfe1daaf3485bc0)
- Introduced six new terms related to AI, such as ANTHROPIC, Entrypoint, OpenAI, TOGETHERAI, XAI, and yml, expanding the wordlist to better support text analysis tasks involving A... [cd01dd06](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/cd01dd067c5cfb0fd9fc21a5df1855b18e7bf266)

### Changed

- Upgraded pre-commit configuration to utilize latest versions of hooks including Pre-Commit, YAML formatter, Black, Isort, Pyupgrade, Ruff, and Markdownlint resulting in users ha... [5dcbb58b](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/5dcbb58bd172cf516da62f59b287d6df4be4d2dc)
- Clarified the integration process for the AI-powered Git hook by enabling users to seamlessly integrate it into their workflows through either adding a local hook or configuring... [41697fe2](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/41697fe21da0aa4f0181a42b0a6b40636f2903c5)
- Updated dependencies to version 6.0.0 for actions/checkout, version 6.1.0 for setup-go and actions/setup-python, version 8.3.0 for super-linter/super-linter, version 7.1.4 for a... [dddad42f](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/dddad42f8ac875ea4ca4aa2bb19521f7121ded54)
- BREAKING: Improved commit message generation for diffs by enabling the utilization of large language models to produce more accurate and context-specific messages. [64238dbd](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/64238dbd83a575e5af22eb75bd7e6a6d05b0c8d0)

## [2.2.0] - 2025-11-28

### Added

- Enabled version management for GitHub Actions by introducing a new script that synchronizes commit hashes used in workflows with their respective upstream repositories ensuring... [a94b61ef](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/a94b61efd2b28612ce5f31e8f14f1a64ebc95b98)

## [2.1.1] - 2025-11-28

### Fixed

- Simplified the commit message template to emphasize clarity and best practices for generating high-quality Git commits, ensuring that generated messages are more readable and se... [1ed1e449](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/1ed1e4499de29adf7feeb3256fc3b62339b61312)

## [2.1.0] - 2025-11-28

### Added

- Enabled generation of high-quality Git commit messages that follow Conventional Commits specification, Google-style, and OpenStack best practices, ensuring self-contained explan... [b90eb9d8](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/b90eb9d83ef52ef36866f400e72ba1340f3aa6cb)

## [2.0.0] - 2025-11-28

### Added

- Enabled users to configure their GitHub Actions and workflows that rely on this wordlist by introducing the inclusion of "repos" as an allowed word in the .wordlist.txt file str... [c0ba432d](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/c0ba432d36a1a3cddeb56237267d061742b472ca)

### Changed

- Modernized the prepare-commit hook entry in pre-commit configuration to accurately reflect its purpose and function without introducing any breaking changes or altering API cont... [e1fda3d3](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/e1fda3d307234dd12d0eb9161007ab6bd89fba37)
- Enabled automated preparation of commit messages using an AI model by introducing a new pre-commit hook that is now included in the default installation stages and configured ac... [4bae3077](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/4bae3077c6b49d4ab7355db4a614c18aa4b959de)
- Refined better compatibility and flexibility in different project structures by updating package discovery to look within the "src" directory and using a relative prompt file pa... [507c9dc0](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/507c9dc0a2bb2b99a823f697040bec1e30f20b18)
- Simplified the API by replacing the deprecated /v1/legacy endpoint with the modern /v2/current endpoint, reducing potential compatibility issues for clients and streamlining int... [98263a8f](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/98263a8fd26d5399ce3424369547345d4086126b)

### Fixed

- BREAKING: Stabilized error handling for invalid flags in the cli module to provide a single user-friendly error message improving overall robustness and usability, note that existing usag... [490d3131](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/490d31316956a82d1465d74859953e7b0ec23c1b)

## [1.0.3] - 2025-11-27

### Fixed

- Resolved pylint issues by removing an unnecessary import and simplifying the code for calling `litellm.completion`, resulting in no breaking behavior, API changes, or config sch... [710e1be1](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/710e1be1b2f9f995284092a9df19c097d87a99bb)

## [1.0.2] - 2025-11-27

### Fixed

- Resolved unnecessary errors in test runs by skipping unused issues in certain test cases within the test_Git.py file. [f60f276c](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/f60f276c90177cf3949aa3f857b5ea8829e82e4d)

## [1.0.1] - 2025-11-27

### Changed

- Simplified the project's readme formatting to clearly convey grammatical and structural relationships through applied semantic line breaks according to the SemBr specification. [c79b4864](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/c79b4864ce80855cffbf9bb1fa53185230eabf33)
- Enabled formatting and testing tools in the project, introducing a new `fmt` command for codebase formatting, as well as tox environments for testing. [738d0c59](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/738d0c5999d472231c3adbfd48f3cbdeef64b901)
- Refined spell checking for Markdown files through reviewdog and pyspelling tools, with configuration in .Github/workflows/spell.yml and dependencies managed in pyproject.toml. [294784a6](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/294784a6ae3be40394a3e6b5a8643cd5b453b504)
- Optimized optional debug logging in the AI prepare commit message module through an added `verbose` flag in its command-line interface and improved handling of non-standard paths... [610618d4](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/610618d451f0c0d7e1563a5b027285ad8bbe6dbd)
- Improved and modernized the project's API for generating commit messages to integrate seamlessly with LiteLLM-style APIs, enabling developers to leverage improved functionalit... [fb1ecda1](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/fb1ecda171e4ae0dbe7b0e66f4817c2741b4ffc8)
- Modernized strict code formatting and linting standards across the project via an integrated GitHub Actions workflow that checks lines of code, external links, syntax, and enforces... [7fe98a92](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/7fe98a920af32c069592e1936b679a85d030c4a8)
- Enhanced the readme file to include additional badges and metrics that provide more insight into the project's code quality and usage. [d9addc43](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/d9addc430247f24ff0465e681122471d994e0d56)
- Test coverage and maintainability have been significantly enhanced by introducing comprehensive test cases for the `GitRepository` and `LanguageModel` classes to handle various... [6cbd32e4](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/6cbd32e4cec2ded6e3675b53c5d6a62fb71055f6)

### Fixed

- Resolved compatibility issues with the latest library version by updating test suite to correctly handle changes in `DummyRepo`'s interface and fixed missing return statements i... [fde4d3f2](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/fde4d3f25364aaf24098ba1d15b9d5974caf57ea)

### Removed

- The term 'YAML' has been excluded from the GitHub Action wordlist used for filtering sensitive information in pull requests and issues. [8b6d0f44](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/8b6d0f4474989bb64efb32b2fe7ddc939acc7171)

## [1.0.0] - 2025-11-26

### Added

- Enabled support for AI-powered generation of Git commit messages through the introduction of a new CLI command and configuration files. [842d6be8](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/842d6be81901b7df7c53ed030f87e60e1141508e)
- Introduced automatic formatting of Python files using Black, Isort, Pyupgrade, Ruff, and Ruff-Format before each commit, ensuring consistent formatting across all project files. [068eb68f](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/068eb68f7eda4e6fa704d13c414fa2556667f925)
- Unlocked multi-language development environments for Docker, Node, Python, Ruby, and UV projects by introducing increased CPU and memory requirements for hosts running the dev co... [eda7d6cb](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/eda7d6cbb66560e65a18eec15534402395f83e7f)
- Delivered strict formatting guidelines for Readme files by introducing a new Markdownlint hook that excludes line length checks and enforces consistent formatting to improve reada... [6737e7a2](https://Github.com/electrocucaracha/ai-prepare-commit-msg/commit/6737e7a2a9d2cff85614bab52d0de52a6e02ba4d)
