
# Sandbox Sample Data Files

This folder contains sample data files ingested by ITS DataHub through programmatic ingest mechanism.

## Wyoming DOT Samples
ITS DataHub ingests and maintains storage of data files from Wyoming DOT (WYDOT). The following sections provide a brief summary of WYDOT data files in their various historical schemas. Each data file contains one sample record.
### Basic Safety Message (BSM) Files
- wydot-filtered-bsm-schemaVersion3.json
- wydot-filtered-bsm-schemaVersion5.json
- wydot-filtered-bsm-schemaVersion6.json

### Traveler Information Message Files

 - wydot-filtered-tim-schemaVersion3.json
 - wydot-filtered-tim-schemaVersion5.json
 - wydot-filtered-tim-schemaVersion6_multi.json
 -- This file contains TIM data where array elements contain multiple elements. Such arrays are represented in the schema as JSON arrays.
 - wydot-filtered-tim-schemaVersion6_single.json
 -- This file contains TIM data where array elements contain a single element. Such single-element arrays are represented as a single JSON object/dictionary.

