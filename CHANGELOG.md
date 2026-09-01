<!-- Repeated section headings (Added/Changed/Fixed) per release are expected
     in the Keep a Changelog format, so MD024 is disabled for this file. -->
<!-- Markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [14.0.0] - 2026-09-01

### Removed

- Simplified configuration by removing explicit 'secrets: inherit' lines from workflow jobs, which are now inherited by default in reusable workflows. [7377f774](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/7377f7745283594d6bd726c151b46052ad7c7c9a)

## [13.0.1] - 2026-09-01

### Changed

- Updated multiple dependencies in uv.lock to their latest versions, including ast-grep-cli, boto3, botocore, filelock, litellm, platformdirs, and regular expression, to ensure alignment with upstream bugfixes and improvements. [086e0ee5](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/086e0ee51728b574d6a67d328be79c1dc9aa9e8e)

## [13.0.0] - 2026-09-01

### Removed

- Simplified CI workflow configuration by removing redundant secrets inheritance from GitHub workflows. [20f62fef](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/20f62fefb087f103463bd7a2a5d6d245449d8eac)

## [12.1.1] - 2026-09-01

### Changed

- Updated GitHub Actions workflows to reference the v5.0.0 release instead of a commit hash on the main branch, and optimized version resolution logic to output release tags instead of commit hashes, improving maintainability and alignment with workflow versioning best practices. [6c16b227](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/6c16b227637d784b2541c12a6d9881f99ba23e35)

## [12.1.0] - 2026-09-01

### Added

- Enabled mypy linter environments to ignore missing imports for certain packages during CI, ensuring more accurate type checking and eliminating false-positive errors. [373bdc8a](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/373bdc8aab1762add044a6cc6ce431e4699fcb7c)

## [12.0.2] - 2026-09-01

### Changed

- Hardened supply chain security by pinning reusable workflows to specific commit hashes in GitHub Actions configuration. [e7e10d45](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/e7e10d45c574c676bfd59c67e4ab5dbe102fc7ce)

## [12.0.1] - 2026-08-31

### Changed

- Simplified explanations for prompt compression and summarization, including Headroom integration and system execution flow, to prioritize developer usability and project guardrails. [29cf66cb](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/29cf66cb42313c56e9f63164f35035969f00d3df)

## [12.0.0] - 2026-08-31

### Removed

- Simplified the codebase by removing unnecessary suppressions and addressing underlying issues, resulting in improved code quality and adherence to best practices. [e7ea07e9](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/e7ea07e95db2ed350a4361907b7ca2e9da88538b)

## [11.0.0] - 2026-08-31

### Removed

- Simplified the project's dependencies by removing the unused aiohttp and python-dotenv packages, which are already transitively included by litellm, resulting in a more streamlined dependency list with no observable impact on API or CLI usage. [58d10ffd](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/58d10ffd6a1299233fba8cea310e3ac3e86cdf7e)

## [10.2.0] - 2026-08-31

### Added

- Enabled comprehensive code coverage of 100% by adding targeted unit tests that cover previously untested code paths in ai_prepare_commit_msg, git.py, and llm.py, including CLI confirmation flow, Git repository interactions, and LLM-related functions. [09a28aec](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/09a28aec7d784a08069e21d113dd44fec516b65d)

## [10.1.1] - 2026-08-31

### Changed

- Enabled comprehensive codebase quality improvements through the introduction of standardized automated refactoring and testing practices facilitated by the Universal Janitor and QA subagent guidelines. [8285c7b9](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/8285c7b993bf1992da8e63cc3409ead56617f3a0)

## [10.1.0] - 2026-08-29

### Added

- Enabled selection of GitHub Copilot models through LiteLLM using the `github_copilot/` provider prefix, allowing users to choose from various models supported by their LiteLLM version and GitHub Copilot account. [22dd98da](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/22dd98da95d13ab2bd4cad8cba9a8d3bbf01cf20)

## [10.0.0] - 2026-08-29

### Removed

- Optimized LLM requests to litellm.completion by enabling the client to filter out unsupported parameters, reducing failures caused by parameter rejection, and removing explicit temperature and num_ctx arguments. [d2e44c9e](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/d2e44c9e7781fa12b9d073d582a252c28af595dc)

## [9.0.4] - 2026-08-29

### Changed

- Clarified the system prompt to provide more detailed guidance for generating commit messages, emphasizing writing for future maintainers and ensuring Conventional Commit compliance. [3651b469](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/3651b469218f84e77375b7055f167a8de0109e47)

## [9.0.3] - 2026-08-29

### Changed

- Upgraded dependencies to ensure compatibility and improved stability, including bugfixes and minor improvements from upstream, with no breaking changes expected but downstream consumers should test integrations as a precaution. [6535e8d7](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/6535e8d7186b854ccd23ae28327b0db7d18b95f6)

## [9.0.2] - 2026-08-29

### Changed

- Switched the prepare-commit hook to run as a shell command, improving compatibility and reducing dependency on Python in environments where it's not available or desired. [50ef55ee](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/50ef55ee4a7b0c9dad80eec24505d85d71738d6a)

## [9.0.1] - 2026-08-29

### Changed

- Expanded the changelog with detailed release entries for versions 8.0.0 through 9.0.0, and enhanced the wordlist with new abbreviations and technical vocabulary to improve spell checking and linting accuracy, thereby increasing project transparency and developer experience. [13227727](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/13227727c959d222e6432565507344a9b36e0b1a)

## [9.0.0] - 2026-08-29

### Removed

- BREAKING: Migrated local workflow logic for linter, release, and update automation to upstream reusable workflows from electrocucaracha/gh-workflows, requiring customizations to be made upstream due to a breaking change. [05a7864a](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/05a7864a12319a5b24bcaa41a1c7599f9162d87f)

## [8.1.0] - 2026-08-29

### Added

- enabled support for custom LiteLLM providers via entry points, allowing integration with corporate gateways or self-hosted servers without modifying the core codebase. [c4f4da09](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/c4f4da0969eff567423410baf2ae73e9f9560a10)

## [8.0.2] - 2026-08-29

### Changed

- Enabled extensibility and transparency in the model routing architecture by introducing a plugin system for custom LLM providers, allowing users to register and integrate private or unsupported backends without modifying the project. [bea11b91](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/bea11b91ad87b963169fb3b629178bca3458aad5)

## [8.0.1] - 2026-08-28

### Changed

- Expanded the wordlist to include new project-specific terminology, abbreviations, and common words, enabling better spell checking and linting accuracy for technical documentation and code comments, particularly for current workflows. [e4ca8fb5](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/e4ca8fb5a9fabad13bff4125714cf86ce71c26e7)

## [8.0.0] - 2026-08-28

### Removed

- Simplified the fake_summarize function in a test by removing an unused content parameter, clarifying the test's intent without affecting test behavior or coverage. [8e17676c](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/8e17676ca92bbead0181c9827e1dbdc7d218e75c)

## [7.10.0] - 2026-08-28

### Added

- Expanded the changelog with detailed entries for all releases from 7.2.1 to 7.9.2, documenting added features, optimizations, and dependency updates, which improves traceability and helps users understand the project's evolution. [6446470e](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/6446470efbfffc03c6ca26cb371efdfa312f36d7)

## [7.9.2] - 2026-08-28

### Changed

- Clarified and streamlined the documentation to improve user discoverability and experience by providing more comprehensive guides and explanations on advanced features, removal steps, and configuration options. [78152d64](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/78152d6462d00fa23e66bbf9f789ea9e18459391)

## [7.9.1] - 2026-08-28

### Changed

- Optimized the pre-commit hook to execute in a consistent and isolated Python environment, reducing dependency conflicts and improving reproducibility across different developer setups. [e11c1fae](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/e11c1faef258695d3530bd274cd424d5a8536c1a)

## [7.9.0] - 2026-08-28

### Added

- Improved diff summarization preserves actionable context for human reviewers by labeling summaries by file path and skipping low-signal files, reducing hallucinated or omitted changes. [211c0af4](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/211c0af443982c1eedbd62b6e389354408dcb7ee)

## [7.8.0] - 2026-08-27

### Added

- Automated release management has been enabled, streamlining the release process with consistent changelog formatting and generating GitHub releases with the latest changelog section as release notes. [8c2cfee1](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/8c2cfee177b637c9483d9ce691648872a04dccbb)

## [7.7.1] - 2026-08-27

### Changed

- Upgraded several pre-commit hooks and Python dependencies to their latest compatible versions, ensuring continued support for new Python versions and features. [e08d4d89](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/e08d4d89be00fdbde8167b1e8eeb854783bc950f)

## [7.7.0] - 2026-08-27

### Added

- Enabled a map-reduce summarization chain for oversized diffs to automatically shrink them before falling back to the oversized diff warning, improving usability for large diffs and reducing manual intervention. [3ba8c5f6](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/3ba8c5f6c60f18601a5e674bb73b776f2b4bb375)

## [7.6.1] - 2026-08-21

### Changed

- Simplified the ignore array in the .jscpd.json file to a single line, improving readability and consistency with the rest of the file. [d6648537](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/d6648537015d1aa8e1e87c919646fd8f7132bfcf)

## [7.6.0] - 2026-08-21

### Added

- Optimized code duplication checks by excluding Markdown files, reducing noise in reports and focusing analysis on source code without impacting build or runtime behavior. [06e7574d](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/06e7574d5e403e90db7b89b77dec02eee68ae6b7)

## [7.5.0] - 2026-08-21

### Added

- Optimized textlint checks to exclude irrelevant files, improving the signal-to-noise ratio in linting results by focusing on relevant documentation and source files. [b82e1c59](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/b82e1c59226893b0d1de9adffc59e2bda83331a2)

## [7.4.1] - 2026-08-21

### Changed

- Dependencies were updated to their latest versions, including uv and aiohttp, to improve performance and compatibility. [71334585](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/71334585f40f1b5931e21ffe574ebbb0730f0e5a)

## [7.4.0] - 2026-08-21

### Added

- Enabled project sponsorship links, allowing users to support ongoing development via GitHub Sponsors and Buy Me a Coffee, with no functional changes to the codebase. [12d32ad0](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/12d32ad028cef66d695bc6f702e62168edd19e57)

## [7.3.0] - 2026-08-18

### Added

- Optimized LLM prompts by applying Headroom prompt compression, reducing token usage and improving efficiency, and introduced metrics to track token savings and requests. [f8446a60](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/f8446a60634d0f159f05f5af45f9e43bff403c3d)

## [7.2.5] - 2026-08-18

### Changed

- Optimized documentation for advanced usage, provider switching, and large-diff handling by adding a new explanation for Headroom prompt compression, updating the "How it works" article, clarifying installation instructions, and expanding configuration options. [cf0a7a13](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/cf0a7a13903f0305bee2913834f1c0cfe27344bf)

## [7.2.4] - 2026-08-15

### Changed

- Enhanced the readme to provide a clear and compelling rationale for using AI Prepare Commit Message, highlighting its benefits of saving time, improving consistency, and streamlining integration with Git workflows. [125a6ebb](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/125a6ebb328cf117601d2f692ed352e4824045a5)

## [7.2.3] - 2026-08-15

### Changed

- Modernized versions files to reflect the latest dependencies, including aiohttp, aiosignal, and uv, requiring users to update their versions accordingly. [052c79b9](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/052c79b99ee8cca6e841e0e610d6bf9500a9f2de)

## [7.2.2] - 2026-08-12

### Changed

- Expanded the custom dictionary to improve spell checking accuracy and support for project-specific terminology, introducing new terms and updating capitalization for several entries without introducing breaking behavior or requiring migration steps. [c81f7449](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/c81f7449d4298dd496197334c8d956302be2d3ea)

## [7.2.1] - 2026-08-12

### Changed

- Expanded the changelog to provide detailed release history, reorganizing sections for clarity and completeness, and restoring missing entries for patch versions. [3e89d8f9](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/3e89d8f93eb0f2373e846306865011f63a765755)

## [7.2.0] - 2026-08-12

### Added

- Enabled automatic textlint integration with the terminology rule for consistent terminology across documentation and code comments, eliminating the need for sudo in node_modules cleanup and streamlining formatting steps. [49fc4ffb](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/49fc4ffb239c7380f7d89f3a73ca80bba61fd95c)

## [7.1.0] - 2026-08-06

### Added

- Enabled detailed changelog entries for versions 7.0.1, 7.0.0, 6.6.0, 6.5.2, 6.5.1, 6.5.0, and 6.4.1, documenting improvements in spell checking accuracy, codespell configuration, linter integration, navigation fixes, dependency upgrades, and wordlist expansion. [11de1dd4](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/11de1dd4511da304d20183972335710324c18bf7)

## [7.0.1] - 2026-08-06

### Changed

- Optimized spell checking accuracy by refining the custom wordlist to exclude common false positives and ensuring relevant files are scanned without introducing any breaking behavior or API changes. [c33cc8ce](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/c33cc8ce500b619b15f396359efa27e4436ecc50)

## [7.0.0] - 2026-08-06

### Removed

- Simplified configuration management by removing redundant custom codespell settings and aligning spell checking with project conventions, allowing for future adjustments via command-line options or a new configuration file if needed. [0475cb08](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/0475cb086cda5f9c4f934770f8c94392df9357c8)

## [6.6.0] - 2026-08-06

### Added

- Enabled more accurate and consistent spell checking during linting by introducing the project's customized codespell configuration to the linter workflow and Makefile. [e259f6af](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/e259f6afd31c7949f66b72fd972e5c75a175663b)

## [6.5.2] - 2026-08-06

### Changed

- Corrected the configuration reference link in tutorials to ensure navigation accuracy for users following the documentation without requiring any migration steps or changes to API or CLI contracts. [c154f82a](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/c154f82a3163425dbd5567848e1c60aeb0339128)

## [6.5.1] - 2026-08-06

### Changed

- Upgraded several GitHub Actions and pre-commit hooks to their latest versions addressing security advisories and benefiting from upstream bugfixes resulting in improved performance and compatibility with recent language and formatting standards without introducing any breaking changes. [f7184842](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/f7184842d0116f441e9033501f3861c4bc6ceb52)

## [6.5.0] - 2026-08-06

### Added

- Expanded the wordlist for validation and testing scenarios by introducing new entries including acb, bafc, beh, dca, Dockerfile, and fbb without modifying existing ones. [5d398bfa](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/5d398bfafee427bdeef33946b3a254e135836f97)

## [6.4.1] - 2026-08-06

### Changed

- Optimized spell checking by expanding the codespell skip list to exclude irrelevant files and updating the changelog with new release entries for versions 6.4.0, 6.3.2, 6.3.1, and 6.3.0 to reflect recent improvements to spell checking, branding consistency, and workflow automation. [40fe6237](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/40fe62379c17e47c19e0805b5c471d02875d20aa)

## [6.4.0] - 2026-08-06

### Added

- Enabled exclusion of CHANGELOG.md from spell checks to prevent false positives and reduce noise in CI results due to intentional spelling variations or external content. [8d439379](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/8d4393794546e55d24e7afe87dca5f2f34919506)

## [6.3.2] - 2026-08-06

### Fixed

- Stabilized the changelog's branding and documentation standards by standardizing the capitalization of tool names throughout the document. [7828ba55](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/7828ba55399f5c67e212bafc28d9bb13fd45423b)

## [6.3.1] - 2026-08-06

### Changed

- Automated pull request creation and Dockerfile updates now successfully complete due to resolving permission issues caused by insufficient permissions with the switch to WORKFLOW_TOKEN as an environment variable. [f3acb649](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/f3acb649be0034114108459727e3b47061388ea1)

## [6.3.0] - 2026-08-06

### Added

- Enabled more accurate spell checking and linter results by expanding the wordlist to include project-specific terms, library names, configuration file extensions, and common abbreviations. [856b2a82](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/856b2a821786804fbb3009dd272960019a85e92b)

## [6.2.0] - 2026-08-06

### Added

- Introduced a comprehensive CHANGELOG.md file that tracks all notable changes, additions, removals, and fixes throughout the project's lifetime following the Keep a Changelog format and adhering to Semantic Versioning. [733c2f9f](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/733c2f9f8deee495520539b681adf6812daf066a)

## [6.1.3] - 2026-08-05

### Changed

- Stabilized GitHub Action workflow updates by introducing a dedicated function for resolving commit hashes and explicitly handling exceptions and pinned actions. [71ed1bdb](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/71ed1bdb34a6184e23a0f1749f42d1d05b691e36)

## [6.1.2] - 2026-08-05

### Changed

- Streamlined scheduled dependency updates by enabling concurrent runs and utilizing latest major action versions to ensure fresh environments and improved reliability. [48baa307](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/48baa30765b8ecf6cebe5bc7d6974c7d0bfd1f60)

## [6.1.1] - 2026-08-04

### Changed

- Upgraded multiple dependencies to their latest versions, addressing bugfixes, security patches, and new features while ensuring compatibility with upstream improvements and maintaining project stability without introducing breaking changes. [5da4f2a8](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/5da4f2a8922f53ff090e81f06f1dc22bfc9e35db)

## [6.1.0] - 2026-08-04

### Added

- Warns developers of oversized diffs that exceed LLM provider limits, skipping unnecessary API calls and providing clear feedback instead of unclear errors or empty messages. [89dd13f9](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/89dd13f9fd30910403b478521074767673a19bee)

## [6.0.1] - 2026-07-28

### Changed

- Simplified workflow files for GitHub Actions to suppress line-length warnings from yamllint on long lines and removed outdated guides in the `docs/guides/` directory, suggesting a documentation restructuring or migration. [8adbb901](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/8adbb9015eacfbb165d41a51c88ee897230fffb8)

## [6.0.0] - 2026-07-24

### Removed

- The conditional check for an empty commit_hash variable now correctly handles whitespace and unset values without potential misbehavior due to double quotes. [a1f542af](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/a1f542afe2270a2225147651f01e15fe916b56b8)

## [5.4.3] - 2026-07-24

### Changed

- Simplified internal test structure and callback configuration to improve maintainability without altering functional behavior. [21a72d69](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/21a72d69d09b010e524eff68b54295a379523ff8)

## [5.4.2] - 2026-07-24

### Changed

- Dependencies were updated to include aiohttp version 3.14.3 and other dependencies like annotated-types and anyio, requiring no breaking behavior or API changes but possibly necessitating migration steps for users. [d36dbc3b](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/d36dbc3bafadd8d89522b3f6cb5bc26277a5687a)

## [5.4.1] - 2026-06-18

### Changed

- Updated Python dependencies to versions 3.14.1 for aiohttp and 4.14.0 for anyio, requiring potential migration steps from users relying on prior package versions. [36b90605](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/36b906055bc054b4f0e7e7488781fcd786ca37aa)

## [5.4.0] - 2026-06-18

### Added

- Enabled better spell checking in documentation and code comments by incorporating 'nav', 'walkthrough', and 'walkthroughs' into the project's wordlist without introducing any breaking behavior or migration requirements. [d24b7bed](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/d24b7bed8136a6695ba20c3a1297b039038562b4)

## [5.3.1] - 2026-06-18

### Changed

- Modernized documentation structure for improved user experience by replacing outdated sections and categories with more descriptive and navigable ones. [543c78b1](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/543c78b1c5339e9c591eea6a8b78a1e611e6297f)

## [5.3.0] - 2026-06-18

### Added

- Optimized the CLI to include retry logic for generating commit messages and enabled Headroom prompt compression with LiteLLM when available. [52e93b8e](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/52e93b8ece6f917eca6e84080aa86dccb55a3a8f)

## [5.2.0] - 2026-06-05

### Added

- Improved the AI assistant's commit message prompt to provide explicit guidance on using semantic line breaks, ensuring each sentence appears on its own line and long sentences are split at natural clause boundaries, thereby enhancing readability and consistency of generated commit messages. [2f9edb3f](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/2f9edb3fdb1163c036f0e100e4f136fcc4071a44)

## [5.1.0] - 2026-06-05

### Added

- BREAKING: Modernized the commit message prompt to include "revert" and "style" types and refined guidelines for better clarity and consistency, requiring updates to existing commit message validation logic due to a breaking change that may affect users' commit message validation processes. [53b94c6f](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/53b94c6f6578c4b4eae4ec685922c671381d639d)

## [5.0.4] - 2026-06-05

### Fixed

- Resolved transient network errors in production by increasing the default maximum attempts for retries from 3 to 5, aligning with observed failure rates and reducing false-positive alerts. [6017f17b](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/6017f17bdf75bda958ea9ad99dec12f866a211e1)

## [5.0.3] - 2026-06-04

### Changed

- Updated aiohttp to 3.14.0 to remediate Trivy-reported CVEs in CI builds without introducing any breaking behavior or API changes. [9eaf6485](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/9eaf64854f25b130d5cbf261e9b3d52b5603fd92)

## [5.0.2] - 2026-05-22

### Changed

- Enabled mypy lint runs to successfully complete even in cases where PyYAML type stubs are missing by allowing the import of YAML with a specific ignore comment. [63044b79](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/63044b7965322724c291fa7f24fea3c18bd44499)

## [5.0.1] - 2026-05-17

### Changed

- Updated dependencies to latest versions including aiohttp 3.13.5 without introducing any breaking behavior or requiring migration actions. [d284aab0](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/d284aab0b452c7f83ca64601f90ba8357f572f76)

## [5.0.0] - 2026-05-17

### Removed

- Simplified the readme by removing redundant documentation about project documentation location to avoid duplication of information and improve clarity. [164e9f32](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/164e9f32c65e3dddc5f2c6ce4e52f19f251574f3)

## [4.1.0] - 2026-05-17

### Added

- Enabled interactive confirmation for generated commit messages by prompting users to accept the message before writing it unless the --auto-approve flag is set or the AI_PREPARE_COMMIT_AUTO_APPROVE environment variable is present. [f233a154](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/f233a1542afcfe05e9a8b64fcdde4b532485607b)

## [4.0.2] - 2026-05-17

### Changed

- Updated the wordlist used for spelling and linting checks to include new terms such as "chmod", "cp", "symlink", and "Lifecycle" which were reordered for consistency with existing entries like "OpenStack". [6f54e1a8](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/6f54e1a8fb4f697524aa6c02118ed9bfe687b600)

## [4.0.1] - 2026-05-17

### Changed

- Modernized type hints and path management by adopting pathlib.Path and built-in generics for improved readability and consistency, without introducing breaking changes that require migration steps. [7a0757ec](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/7a0757ec42395f654c812258a7d942367ed7eb32)

## [4.0.0] - 2026-05-17

### Removed

- Simplified the formatting process by removing pyink and relying on black, isort, and ruff to eliminate redundancy and potential conflicts between formatters. [ec089db4](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/ec089db412e5acd360a2da0c6246755d1023a618)

## [3.0.1] - 2026-05-17

### Changed

- Stabilized comprehensive Python coding standards by introducing a new instructions document that outlines style guidelines, formatting conventions, type annotations, docstrings, testing practices, and idiomatic usage, referencing Raymond Hettinger's best practices. [6ad20eab](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/6ad20eab4265722b3db9eab0d584d084d1c008be)

## [3.0.0] - 2026-05-17

### Removed

- Simplified repository configuration and documentation by eliminating obsolete instructions for GitHub Copilot and SemBr prompts from repository-specific Markdown files, reducing maintenance overhead and avoiding confusion about current project workflows and requirements. [762f9b47](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/762f9b47fa6d007e387078504152ec24adda7ada)

## [2.15.0] - 2026-05-17

### Added

- Enforced project quality gates for contributors by introducing required linting and formatting checks via make lint and make fmt commands that must be addressed before finalizing changes. [77063f6d](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/77063f6d1bf9753cf3a4d1eb2ee4bb4cf3f940cf)

## [2.14.0] - 2026-05-17

### Added

- Enabled mandatory testing for Python changes by formalizing test requirements in documentation to ensure high standards of code integrity through rigorous testing. [4967f5f0](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/4967f5f032fcc18032e8537e5eb41ebc8d23b4db)

## [2.13.0] - 2026-05-17

### Added

- Enabled semantic line breaks in Markdown files to improve editability and consistency by specifying safety constraints and output style expectations while preserving rendered output and meaning. [84a88415](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/84a88415530917de490617896ffd15b3b4f3845d)

## [2.12.3] - 2026-05-17

### Changed

- Simplified and modernized documentation structure to improve discoverability and maintainability, providing clear entry points for learning, doing, and reference through the reorganized docs/ directory on GitHub Pages. [57091f79](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/57091f7969ffd27d5260ee3524391a52322af940)

## [2.12.2] - 2026-05-17

### Changed

- Updated pre-commit configuration to leverage the maintained markdownlint-cli for better compatibility and ongoing support by switching from the deprecated Ruby gem and adopting a more flexible configuration approach via markdownlint config files or CLI options. [18996f52](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/18996f52f55a352b9d3344d4f1dedb6966e65483)

## [2.12.1] - 2026-05-17

### Changed

- Refined the AI-powered Git hook's commit message generation prompt to align with OpenStack best practices, requiring users to write commit messages that follow Conventional Commits and OpenStack guidelines by focusing on primary behavior changes and providing clear explanations. [ff92e528](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/ff92e52823533d4f5b61f5fb8b935b66c32666fa)

## [2.12.0] - 2026-05-17

### Added

- Enforced strict adherence to Conventional Commits syntax for user-generated commit messages by updating the commit message prompts and validation checklist. [be13b69b](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/be13b69be39dac83d2b1849ff98612fa222fcddf)

## [2.11.6] - 2026-05-08

### Fixed

- Resolved sensitive WORKFLOW_TOKEN exposure by securely passing it through environment variables in GitHub Actions workflows. [57ffd140](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/57ffd1405924df2aa264e5930881c26a87461be7)

## [2.11.5] - 2026-05-08

### Fixed

- Resolved zizmor secrets-outside-env warnings and CVEs in GitPython by upgrading it to version 3.1.50 and adding the versions-update environment variable to the check-versions job. [1b2c93a9](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/1b2c93a903e64c73485486b0abf51144f6aff2bd)

## [2.11.4] - 2026-05-01

### Changed

- Resolved CVE-2026-28684 by upgrading python-dotenv to its latest version, ensuring the project's dependencies are secure and up-to-date with no breaking changes required for users. [0dd22039](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/0dd22039e00b2d626d73a752f5aad511e38b4ed2)

## [2.11.3] - 2026-04-24

### Changed

- Standardized GitHub Actions workflows to ensure consistent pinned versions across lint, spell check, and update tasks while preserving repository-specific behavior. [de95b380](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/de95b380b86dba1b926b301b44782e44acca126f)

## [2.11.2] - 2026-04-11

### Fixed

- Resolved formatting issues in copilot-instructions.md to improve readability and maintainability for users following these instructions. [86f73a73](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/86f73a73593d9dae19d23c37cb4d7bf8210d44c0)

## [2.11.1] - 2026-04-02

### Changed

- Updated dependencies to version 3.13.5 for aiohttp, 4.13.0 for anyio, 26.1.0 for attrs, and left beautifulsoup4 at 4.14.3 unchanged. [8427073b](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/8427073bce746c63560ead82a1cd27a0d34b420e)

## [2.11.0] - 2026-04-02

### Added

- BREAKING: Enabled finer-grained control over logging verbosity by introducing a --log-level option that replaces the --verbose flag and accepts DEBUG, INFO, WARNING, ERROR, and CRITICAL levels, requiring users to update their pre-commit configs and documentation. [b39ae713](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/b39ae7133afd8011f2568a0192c47246d6f67458)

## [2.10.0] - 2026-04-02

### Added

- Introduced support for GitHub models by allowing users to configure the LITELLM_PROXY_MODEL environment variable for models like GitHub Copilot or GPT-4 without breaking any existing behavior. [b02506a2](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/b02506a2c57e723eb7123f295eaea2cfa9e5356f)

## [2.9.0] - 2026-04-02

### Added

- Enabled repository maintainers to guide developers in generating high-quality code through the introduction of copilot instructions that outline Pythonic best practices and pre-commit requirements. [05076ec3](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/05076ec3b7f3a7cc030b1bb589f313fa3c8871f7)

## [2.8.0] - 2026-04-02

### Added

- Enabled a timeout for LLM calls in the commit message generation process to prevent model timeouts and allow fallbacks when necessary. [ad1b281c](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/ad1b281cdcffc15c960669a6c5f1c5d5cd4e47e9)

## [2.7.6] - 2026-03-30

### Changed

- Updated super-linter to v8.5.0 and replaced archived action technote-space/get-diff-action with a native Git diff step to resolve template injection issues and hardened CI workflows against vulnerabilities in Python packages. [d0137355](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/d0137355f835bb4a1fd1d18a77106c97e93e2a09)

## [2.7.5] - 2025-12-11

### Changed

- Updated dependencies for uv, aiohttp, and other packages to their latest versions available on PyPI, providing users with access to the newest features and bugfixes in these libraries. [3daa7bfd](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/3daa7bfddb8023c82528bb786ee2be3b6d34cef3)

## [2.7.4] - 2025-12-12

### Changed

- Upgraded versions of several dependencies to their latest available releases, including ruff 0.14.9, openai 2.11.0, huggingface-hub 1.2.2, litellm 1.80.9, and urllib3 2.6.2. [57fd05f5](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/57fd05f556172ea9e380e404c3fa76ce5f492f0a)

## [2.7.3] - 2025-12-08

### Changed

- Updated versions files to reflect the latest available dependencies on PyPI, including added constraints for Python 3.12 and earlier, requiring potential migration steps from users with customized dependencies. [a734128e](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/a734128efe0cda973fdfe1c689cf3872ec666702)

## [2.7.2] - 2025-12-07

### Changed

- Updated actions/checkout to version 6.0.1 in GitHub workflows, allowing existing configurations to remain compatible without requiring manual intervention for the minor version bump. [b290ac40](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/b290ac40527a04280263d8967c36743a290a1010)

## [2.7.1] - 2025-12-05

### Changed

- Enabled GitHub Actions for the project's CI workflow to utilize latest versions of several actions including Markdown link check, super-linter validation, and AI analysis thereby resolving linter failures and providing improved log analysis capabilities. [4b0f4dc0](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/4b0f4dc00f617e84300a173c5f31a258d151950f)

## [2.7.0] - 2025-12-05

### Added

- BREAKING: Enabled explicit control over pre-commit validation by adding `VALIDATE_PRE_COMMIT` to the list of environment variables set to `"false"`, making it clear that this step is disabled in the build process with no migration steps required and no change to the API or CLI contract. [88bc3cb5](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/88bc3cb5dbcdf6431558341626181f983e68ed49)

## [2.6.0] - 2025-12-05

### Added

- Enabled developers to generate completions compatible with LLaMA API by introducing the necessary parameters for temperature, max tokens, and num context. [a77787c4](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/a77787c481f8e1416ebc0c3e10861428ada0052f)

## [2.5.2] - 2025-12-05

### Changed

- BREAKING: Optimized commit message generation for diffs by leveraging large language models to produce more accurate and context-specific messages. [64238dbd](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/64238dbd83a575e5af22eb75bd7e6a6d05b0c8d0)

## [2.5.1] - 2025-12-01

### Changed

- Updated dependencies to versions 6.0.0 for actions/checkout, 6.1.0 for both actions/setup-go and actions/setup-python, 8.3.0 for super-linter/super-linter, 7.1.4 for astral-sh/setup-uv, and 0.14.7 for ruff. [dddad42f](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/dddad42f8ac875ea4ca4aa2bb19521f7121ded54)

## [2.5.0] - 2025-11-28

### Added

- Introduced six new AI-related terms to the wordlist for improved filtering and matching capabilities in the application, without introducing any breaking behavior, API changes, or security concerns. [cd01dd06](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/cd01dd067c5cfb0fd9fc21a5df1855b18e7bf266)

## [2.4.0] - 2025-11-28

### Added

- Enforced project-wide coding style consistency by introducing an .editorconfig file that standardizes indentation to 4 spaces and ignores style rules within the .tox directory. [21ceed33](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/21ceed330843536c93e83160adfe1daaf3485bc0)

## [2.3.2] - 2025-11-28

### Changed

- Clarified installation instructions for the AI-powered Git hook to simplify integration into users' workflows by specifying configuration options via environment variables and .pre-commit-config.yaml file. [41697fe2](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/41697fe21da0aa4f0181a42b0a6b40636f2903c5)

## [2.3.1] - 2025-11-28

### Changed

- Modernized pre-commit configuration to utilize latest versions of hooks including Pre-Commit, YAML formatter, Black, Isort, Pyupgrade, and Ruff which may require users to adapt to new configurations. [5dcbb58b](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/5dcbb58bd172cf516da62f59b287d6df4be4d2dc)

## [2.3.0] - 2025-11-28

### Added

- Enabled automatic version updates for GitHub Actions by synchronizing commit hashes used in workflows with their respective upstream repositories. [a94b61ef](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/a94b61efd2b28612ce5f31e8f14f1a64ebc95b98)

## [2.2.1] - 2025-11-28

### Fixed

- clarified commit message templates to emphasize clear explanations, single logical changes per commit, and proper use of breaking change indicators and semantic line breaks for improved readability and consistency in generated messages. [1ed1e449](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/1ed1e4499de29adf7feeb3256fc3b62339b61312)

## [2.2.0] - 2025-11-28

### Added

- Enabled high-quality Git commit messages that follow Conventional Commits specification, Google-style, and OpenStack best practices by default for newly generated commits, ensuring clarity, maintainability, and compliance with SemBr rules without modifying existing commit history. [b90eb9d8](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/b90eb9d83ef52ef36866f400e72ba1340f3aa6cb)

## [2.1.2] - 2025-11-28

### Fixed

- BREAKING: Stabilized error handling for invalid flags to provide a single user-friendly error message, requiring updates to existing usage due to the changed error message format. [490d3131](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/490d31316956a82d1465d74859953e7b0ec23c1b)

## [2.1.1] - 2025-11-28

### Changed

- Simplified client interactions by replacing the outdated /v1/legacy endpoint with the modern and consistent /v2/current endpoint throughout the system. [98263a8f](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/98263a8fd26d5399ce3424369547345d4086126b)

## [2.1.0] - 2025-11-27

### Added

- Enabled explicit listing of repositories in the .wordlist.txt file structure, requiring no breaking changes or API updates but potentially affecting workflows reliant on the previous organization. [c0ba432d](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/c0ba432d36a1a3cddeb56237267d061742b472ca)

## [2.0.6] - 2025-11-27

### Changed

- Improved package discovery for `setuptools` and optimized prompt file path resolution to enhance compatibility and flexibility in various project structures. [507c9dc0](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/507c9dc0a2bb2b99a823f697040bec1e30f20b18)

## [2.0.5] - 2025-11-27

### Changed

- Enabled automated preparation of commit messages using an AI model through the addition of a new pre-commit hook to the repository's configuration. [4bae3077](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/4bae3077c6b49d4ab7355db4a614c18aa4b959de)

## [2.0.4] - 2025-11-27

### Changed

- The prepare-commit hook in the .pre-commit-hooks.yaml file now uses the prepare-commit entry instead of ai-prepare-commit. [e1fda3d3](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/e1fda3d307234dd12d0eb9161007ab6bd89fba37)

## [2.0.3] - 2025-11-27

### Fixed

- The pylint issues were resolved by simplifying and optimizing the codebase, resulting in no breaking behavior, API changes, or security impacts. [710e1be1](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/710e1be1b2f9f995284092a9df19c097d87a99bb)

## [2.0.2] - 2025-11-27

### Fixed

- The test suite was stabilized by skipping an unused issue from test_git.py to prevent unnecessary testing, which simplifies the test environment without affecting API or CLI contracts. [f60f276c](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/f60f276c90177cf3949aa3f857b5ea8829e82e4d)

## [2.0.1] - 2025-11-27

### Fixed

- Resolved compatibility issues with the latest library version by updating the test suite to ensure correct operation across versions. [fde4d3f2](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/fde4d3f25364aaf24098ba1d15b9d5974caf57ea)

## [2.0.0] - 2025-11-27

### Removed

- The wordlist used for GitHub repository checks has been simplified by removing the term YAML. [8b6d0f44](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/8b6d0f4474989bb64efb32b2fe7ddc939acc7171)

## [1.3.8] - 2025-11-27

### Changed

- Test coverage has been significantly enhanced by introducing comprehensive test cases for various edge conditions and system behaviors in the GitRepository and LanguageModel classes. [6cbd32e4](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/6cbd32e4cec2ded6e3675b53c5d6a62fb71055f6)

## [1.3.7] - 2025-11-27

### Changed

- Enhanced the project's readme file with additional metrics and badges to improve its appearance and informational value for users. [d9addc43](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/d9addc430247f24ff0465e681122471d994e0d56)

## [1.3.6] - 2025-11-27

### Changed

- Enabled strict enforcement of consistent coding standards across the project by introducing a linter workflow that checks lines of code, external links, and syntax using super-linter, Isort, Black, and RUFF tools. [7fe98a92](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/7fe98a920af32c069592e1936b679a85d030c4a8)

## [1.3.5] - 2025-11-27

### Changed

- Simplified generation of commit messages by integrating LiteLLM-style API functionality into a single file, eliminating the need for separate modules and enabling more streamlined interaction with models. [fb1ecda1](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/fb1ecda171e4ae0dbe7b0e66f4817c2741b4ffc8)

## [1.3.4] - 2025-11-27

### Changed

- Optimized the AI prepare commit message module to improve its usability by enabling debug logging through an optional CLI flag and simplifying prompt message management via YAML files. [610618d4](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/610618d451f0c0d7e1563a5b027285ad8bbe6dbd)

## [1.3.3] - 2025-11-27

### Changed

- Enabled spell checking for contributors by configuring GitHub Actions and updating project dependencies to enforce accurate documentation and code submissions. [294784a6](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/294784a6ae3be40394a3e6b5a8643cd5b453b504)

## [1.3.2] - 2025-11-26

### Changed

- Enabled formatting and linting tools through a new Makefile command and pyproject.toml dependency group, simplifying codebase maintenance by introducing automated checks for consistency and style. [738d0c59](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/738d0c5999d472231c3adbfd48f3cbdeef64b901)

## [1.3.1] - 2025-11-26

### Changed

- Optimized the project's readme to provide improved readability and structure through semantic line breaks according to the SemBr specification without altering rendered appearance or interpretation. [c79b4864](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/c79b4864ce80855cffbf9bb1fa53185230eabf33)

## [1.3.0] - 2025-11-26

### Added

- Enabled automated formatting checks for readme files during pre-commit processing, excluding line length restrictions to improve readability without requiring any migration steps or breaking changes. [6737e7a2](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/6737e7a2a9d2cff85614bab52d0de52a6e02ba4d)

## [1.2.0] - 2025-11-26

### Added

- Enabled multi-language development environments for Node, Python, Ruby, and UV projects through the introduction of .devcontainer.json configuration files, which require increased host machine CPU and memory resources to support efficient development workflows. [eda7d6cb](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/eda7d6cbb66560e65a18eec15534402395f83e7f)

## [1.1.0] - 2025-11-26

### Added

- Enabled automatic formatting of Python files using Black, Isort, Pyupgrade, Ruff, and Ruff-Format tools before each commit, ensuring consistent and readable code across the project. [068eb68f](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/068eb68f7eda4e6fa704d13c414fa2556667f925)

## [1.0.0] - 2025-11-26

### Added

- Enabled AI-based generation of Git commit messages through the introduction of custom hooks and configuration files to manage environment variables and cache directories. [842d6be8](https://github.com/electrocucaracha/ai-prepare-commit-msg/commit/842d6be81901b7df7c53ed030f87e60e1141508e)
