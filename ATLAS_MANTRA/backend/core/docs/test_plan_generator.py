"""
MANTRA Test Plan Generator

Generates comprehensive test plans from decisions.

Features:
- Test strategy overview
- Test cases from constraints
- Coverage requirements
- Test data requirements
- Automation guidelines

OUTPUT STRUCTURE:
1. Overview - Test strategy and scope
2. Test Types - Unit, integration, E2E, etc.
3. Test Cases - Derived from constraints
4. Coverage Requirements - What must be tested
5. Test Data - Required test data
6. Automation - What to automate
7. Schedule - Test phases
"""

from typing import List, Dict, Any
from .doc_generator import (
    DocumentGenerator, DocumentType, DocumentSection, DocumentConfig
)


class TestPlanGenerator(DocumentGenerator):
    """Generates Test Plan documents."""

    @property
    def doc_type(self) -> DocumentType:
        return DocumentType.TEST_PLAN

    def generate_sections(
        self,
        decisions: List[Dict[str, Any]],
        config: DocumentConfig
    ) -> List[DocumentSection]:
        """Generate test plan sections."""
        sections = []

        # 1. Overview
        sections.append(self._generate_overview(decisions, config))

        # 2. Test Types
        sections.append(self._generate_test_types(decisions))

        # 3. Test Cases
        sections.append(self._generate_test_cases(decisions))

        # 4. Coverage Requirements
        sections.append(self._generate_coverage(decisions))

        # 5. Test Data
        sections.append(self._generate_test_data(decisions))

        # 6. Automation Strategy
        sections.append(self._generate_automation(decisions))

        # 7. Risk-Based Testing
        sections.append(self._generate_risk_testing(decisions))

        return sections

    def _generate_overview(
        self,
        decisions: List[Dict[str, Any]],
        config: DocumentConfig
    ) -> DocumentSection:
        """Generate test overview."""
        # Count testable constraints
        total_constraints = sum(
            len(d.get("constraints", []))
            for d in decisions
        )
        must_constraints = sum(
            len([c for c in d.get("constraints", [])
                 if isinstance(c, dict) and c.get("type") == "MUST"])
            for d in decisions
        )

        content = f"""## Test Plan Overview

### Scope
This test plan covers testing requirements derived from **{len(decisions)} MANTRA decisions**
containing **{total_constraints} testable constraints** ({must_constraints} MUST requirements).

### Objectives
1. Verify all MUST constraints are satisfied
2. Ensure MUST_NOT violations are prevented
3. Validate system behavior against invariants
4. Confirm integration between decision-covered areas

### Test Strategy
- **Risk-Based Approach**: Prioritize CRITICAL decisions
- **Constraint-Driven**: Test cases derived from decision constraints
- **Automated First**: Automate regression for all MUST constraints
- **Continuous**: Integrate tests into CI/CD pipeline

### Success Criteria
- 100% coverage of MUST constraints
- 100% coverage of MUST_NOT constraints
- 80% coverage of SHOULD constraints
- All CRITICAL decisions tested with integration tests
"""
        return DocumentSection(
            id="overview",
            title="Test Plan Overview",
            content=content,
            level=1,
        )

    def _generate_test_types(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate test types section."""
        content_lines = ["## Test Types\n"]

        # Categorize decisions by scope to determine test types
        by_scope = {}
        for d in decisions:
            scope = d.get("scope_path", "*")
            top_scope = scope.split(".")[0] if scope != "*" else "general"
            by_scope[top_scope] = by_scope.get(top_scope, 0) + 1

        content_lines.append("### Unit Tests")
        content_lines.append("*Test individual components in isolation*\n")
        content_lines.append("| Area | Decision Count | Focus |")
        content_lines.append("|------|----------------|-------|")
        for scope, count in sorted(by_scope.items(), key=lambda x: -x[1])[:5]:
            content_lines.append(f"| {scope} | {count} | Component-level logic |")
        content_lines.append("")

        content_lines.append("### Integration Tests")
        content_lines.append("*Test interactions between components*\n")
        content_lines.append("- API endpoint integration")
        content_lines.append("- Database operations")
        content_lines.append("- Service-to-service communication")
        content_lines.append("- External API integration")
        content_lines.append("")

        content_lines.append("### End-to-End Tests")
        content_lines.append("*Test complete user workflows*\n")
        content_lines.append("- Critical user journeys")
        content_lines.append("- Authentication flows")
        content_lines.append("- Data creation/modification flows")
        content_lines.append("")

        content_lines.append("### Performance Tests")
        content_lines.append("*Validate performance constraints*\n")
        # Extract performance-related decisions
        perf_decisions = [
            d for d in decisions
            if any(t in str(d.get("tags", [])).lower() for t in ["performance", "sla", "latency"])
        ]
        if perf_decisions:
            for d in perf_decisions[:3]:
                content_lines.append(f"- **[{d.get('code', '')}]** {d.get('summary', '')[:60]}")
        else:
            content_lines.append("- Response time under load")
            content_lines.append("- Throughput benchmarks")

        return DocumentSection(
            id="test-types",
            title="Test Types",
            content="\n".join(content_lines),
            level=1,
        )

    def _generate_test_cases(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate test cases from constraints."""
        subsections = []

        # Group by impact for prioritized test cases
        critical = [d for d in decisions if d.get("impact") == "CRITICAL"]
        important = [d for d in decisions if d.get("impact") == "IMPORTANT"]

        # Critical test cases
        if critical:
            content_lines = []
            test_num = 1

            for d in critical[:10]:
                code = d.get("code", "")
                for c in d.get("constraints", [])[:3]:
                    if isinstance(c, dict):
                        rule = c.get("rule", "")
                        ctype = c.get("type", "MUST")

                        content_lines.append(f"#### TC-{test_num:03d}: {code} - {ctype}")
                        content_lines.append(f"**Constraint:** {rule[:100]}")
                        content_lines.append("")
                        content_lines.append("**Test Steps:**")
                        content_lines.append("1. Setup preconditions")
                        content_lines.append("2. Execute action")
                        content_lines.append(f"3. Verify {ctype} constraint is {'satisfied' if ctype == 'MUST' else 'not violated'}")
                        content_lines.append("")
                        content_lines.append(f"**Expected Result:** Constraint {'met' if ctype != 'MUST_NOT' else 'not violated'}")
                        content_lines.append("")
                        test_num += 1

            subsections.append(DocumentSection(
                id="tc-critical",
                title="Critical Test Cases (P0)",
                content="\n".join(content_lines),
                level=2,
                decision_ids=[d.get("code", "") for d in critical],
            ))

        # Important test cases
        if important:
            content_lines = []
            test_num = 100

            for d in important[:10]:
                code = d.get("code", "")
                constraints = d.get("constraints", [])

                if constraints:
                    content_lines.append(f"#### TC-{test_num:03d}: {code}")
                    content_lines.append(f"**Summary:** {d.get('summary', '')[:80]}")
                    content_lines.append("")
                    content_lines.append("**Constraints to Test:**")

                    for c in constraints[:3]:
                        if isinstance(c, dict):
                            rule = c.get("rule", "")[:60]
                            ctype = c.get("type", "MUST")
                            content_lines.append(f"- [{ctype}] {rule}")

                    content_lines.append("")
                    test_num += 1

            subsections.append(DocumentSection(
                id="tc-important",
                title="Important Test Cases (P1)",
                content="\n".join(content_lines),
                level=2,
                decision_ids=[d.get("code", "") for d in important[:10]],
            ))

        return DocumentSection(
            id="test-cases",
            title="Test Cases",
            content="Test cases derived from decision constraints:",
            level=1,
            subsections=subsections,
        )

    def _generate_coverage(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate coverage requirements."""
        content_lines = ["## Coverage Requirements\n"]

        # Calculate constraint breakdown
        must_count = 0
        must_not_count = 0
        should_count = 0

        for d in decisions:
            for c in d.get("constraints", []):
                if isinstance(c, dict):
                    ctype = c.get("type", "MUST")
                    if ctype == "MUST":
                        must_count += 1
                    elif ctype == "MUST_NOT":
                        must_not_count += 1
                    elif ctype == "SHOULD":
                        should_count += 1

        content_lines.append("### Constraint Coverage Targets\n")
        content_lines.append("| Constraint Type | Count | Required Coverage | Priority |")
        content_lines.append("|-----------------|-------|-------------------|----------|")
        content_lines.append(f"| MUST | {must_count} | 100% | Critical |")
        content_lines.append(f"| MUST_NOT | {must_not_count} | 100% | Critical |")
        content_lines.append(f"| SHOULD | {should_count} | 80% | High |")
        content_lines.append("")

        content_lines.append("### Code Coverage Targets\n")
        content_lines.append("| Type | Target |")
        content_lines.append("|------|--------|")
        content_lines.append("| Line Coverage | 80% |")
        content_lines.append("| Branch Coverage | 70% |")
        content_lines.append("| Function Coverage | 90% |")
        content_lines.append("")

        content_lines.append("### Decision Coverage\n")
        content_lines.append(f"- Total Decisions: {len(decisions)}")
        content_lines.append(f"- CRITICAL Decisions: {len([d for d in decisions if d.get('impact') == 'CRITICAL'])} (100% required)")
        content_lines.append(f"- IMPORTANT Decisions: {len([d for d in decisions if d.get('impact') == 'IMPORTANT'])} (80% required)")

        return DocumentSection(
            id="coverage",
            title="Coverage Requirements",
            content="\n".join(content_lines),
            level=1,
        )

    def _generate_test_data(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate test data requirements."""
        content_lines = ["## Test Data Requirements\n"]

        # Extract data requirements from decisions
        content_lines.append("### Data Categories\n")

        # Group by domain for data categories
        domains = set(d.get("domain_id", "OTHER") for d in decisions)

        for domain in sorted(domains):
            domain_decisions = [d for d in decisions if d.get("domain_id") == domain]
            content_lines.append(f"#### {domain} Domain")
            content_lines.append(f"*{len(domain_decisions)} decisions*\n")

            # List what data might be needed
            content_lines.append("Data requirements:")
            for d in domain_decisions[:3]:
                content_lines.append(f"- Data for: {d.get('summary', '')[:50]}")
            content_lines.append("")

        content_lines.append("### Test Data Management\n")
        content_lines.append("- Use factories/fixtures for consistent test data")
        content_lines.append("- Isolate test data per test run")
        content_lines.append("- Clean up test data after each test")
        content_lines.append("- Use realistic but anonymized data")

        return DocumentSection(
            id="test-data",
            title="Test Data Requirements",
            content="\n".join(content_lines),
            level=1,
        )

    def _generate_automation(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate automation strategy."""
        content_lines = ["## Automation Strategy\n"]

        content_lines.append("### Automation Priorities\n")
        content_lines.append("1. **All MUST constraints** - Automated regression")
        content_lines.append("2. **All MUST_NOT constraints** - Automated negative tests")
        content_lines.append("3. **Critical path tests** - E2E automation")
        content_lines.append("4. **Performance tests** - Load testing automation")
        content_lines.append("")

        content_lines.append("### Automation Framework\n")
        content_lines.append("| Layer | Tool | Purpose |")
        content_lines.append("|-------|------|---------|")
        content_lines.append("| Unit | pytest/jest | Component testing |")
        content_lines.append("| Integration | pytest | API testing |")
        content_lines.append("| E2E | Playwright/Cypress | UI testing |")
        content_lines.append("| Performance | k6/Locust | Load testing |")
        content_lines.append("")

        content_lines.append("### CI/CD Integration\n")
        content_lines.append("- Run unit tests on every commit")
        content_lines.append("- Run integration tests on PR merge")
        content_lines.append("- Run E2E tests nightly")
        content_lines.append("- Run performance tests weekly")

        return DocumentSection(
            id="automation",
            title="Automation Strategy",
            content="\n".join(content_lines),
            level=1,
        )

    def _generate_risk_testing(
        self,
        decisions: List[Dict[str, Any]]
    ) -> DocumentSection:
        """Generate risk-based testing section."""
        content_lines = ["## Risk-Based Testing\n"]

        # Identify high-risk areas from MUST_NOT constraints
        content_lines.append("### High-Risk Areas\n")
        content_lines.append("Areas requiring additional testing focus:\n")

        risk_areas = []
        for d in decisions:
            for c in d.get("constraints", []):
                if isinstance(c, dict) and c.get("type") == "MUST_NOT":
                    risk_areas.append({
                        "code": d.get("code", ""),
                        "rule": c.get("rule", "")[:80],
                    })

        if risk_areas:
            content_lines.append("| Decision | Risk (MUST_NOT) |")
            content_lines.append("|----------|-----------------|")
            for risk in risk_areas[:10]:
                content_lines.append(f"| {risk['code']} | {risk['rule']} |")
        else:
            content_lines.append("No high-risk areas identified from MUST_NOT constraints.")

        content_lines.append("\n### Risk Mitigation\n")
        content_lines.append("- Additional test coverage for high-risk areas")
        content_lines.append("- Negative test cases for all MUST_NOT constraints")
        content_lines.append("- Security testing for auth-related decisions")
        content_lines.append("- Performance testing for scalability decisions")

        return DocumentSection(
            id="risk-testing",
            title="Risk-Based Testing",
            content="\n".join(content_lines),
            level=1,
        )


__all__ = ["TestPlanGenerator"]
