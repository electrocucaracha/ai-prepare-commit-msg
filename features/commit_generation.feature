Feature: Generate commit messages
  The command turns staged changes into an approved Conventional Commit message.

  Scenario: Write an approved generated message
    Given staged changes are available
    And the generator produces "docs: explain the BDD suite"
    When the generated message is approved
    Then the command succeeds
    And the commit message is "docs: explain the BDD suite"

  Scenario: Retry an empty generated message
    Given staged changes are available
    And the generator returns empty messages before "fix: recover from a retry"
    When generation is auto-approved with a retry limit of 3
    Then the command succeeds
    And the commit message is "fix: recover from a retry"
    And 2 retry waits occur

  Scenario: Classify a generated message with a decision service
    Given staged changes are available
    And the generator produces "add commit type selection"
    And the decision service selects "feat"
    When generation is auto-approved with a decision service
    Then the command succeeds
    And the commit message is "feat: add commit type selection"

  Scenario: Reject an approved generated message
    Given staged changes are available
    And the generator produces "docs: reject this message"
    When the generated message is rejected
    Then the command fails with "Commit message not approved; aborting commit."
    And no commit message is written

  Scenario: Stop after retry limit is exhausted
    Given staged changes are available
    And the generator returns only empty messages
    When generation is auto-approved with a retry limit of 2
    Then the command fails with "Generated commit message is empty after all retry attempts."
    And no commit message is written
    And 1 retry waits occur

  Scenario: Handle an LLM provider failure
    Given staged changes are available
    And the LLM provider fails
    When generation is auto-approved with a retry limit of 1
    Then the command fails with "Generated commit message is empty after all retry attempts."
    And no commit message is written

  Scenario: Skip generation when no staged changes exist
    Given no staged changes are available
    When generation is auto-approved with a retry limit of 1
    Then the command succeeds
    And no commit message is written