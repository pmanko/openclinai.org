# Component documentation and contracts

OpenClinAI brings together independently maintained applications and a validation
runner. Start with each component's native documentation for setup, supported
interfaces and current application behavior. The public website does not redefine
those contracts. The OpenMRS links below identify the reviewed assembled revisions;
they do not imply an upstream merge or deployed release.

- **ChartSearchAI:** [project documentation](https://github.com/pmanko/openmrs-module-chartsearchai/tree/20cb84ba97bb76ee97a8745016a6d9bb1546077b/docs) and [source/setup](https://github.com/pmanko/openmrs-module-chartsearchai/tree/20cb84ba97bb76ee97a8745016a6d9bb1546077b).
- **ChartSearchAI frontend:** [source/setup](https://github.com/pmanko/openmrs-esm-chartsearchai/tree/475f6eb60ea14011f719c861b02d02daf2156390).
- **QueryStore:** [REST API](https://github.com/pmanko/openmrs-module-querystore/blob/286993cc094499ed29f97d4574775cd2c96f5676/docs/rest-api.md) and [architecture decisions](https://github.com/pmanko/openmrs-module-querystore/blob/286993cc094499ed29f97d4574775cd2c96f5676/docs/adr.md).
- **Med Agent Hub:** [source/setup](https://github.com/pmanko/med-agent-hub).
- **Catalyst:** [application specification](https://github.com/DIGI-UW/catalyst-ai/blob/main/docs/specification.md), [Hub integration](https://github.com/DIGI-UW/catalyst-ai/blob/main/docs/med-agent-hub.md) and [cross-project delivery](../roadmap.md#6-catalyst-delivery).
- **Validation harness:** [setup and experiment commands](https://github.com/pmanko/clinical-ai-validation-harness#readme) and [current validation contract](https://github.com/pmanko/clinical-ai-validation-harness/blob/main/specs/006-validation-harness-mvp/spec.md).

The [workspace roadmap](https://github.com/pmanko/openclinai.org/blob/main/specs/roadmap.md)
coordinates delivery. [Published reports](https://reports.openclinai.org/) and
[recorded demonstrations](https://openclinai.org/catalyst/) describe particular
runs, not current deployment or clinical acceptance. Review provenance, methods,
limitations and human review before using their findings.
