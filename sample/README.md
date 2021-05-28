
# Sandbox Sample Data Files

This folder contains sample data files ingested by ITS DataHub through programmatic ingest mechanism.

## Connected Vehicle Pilots
ITS DataHub ingests and maintains storage of data files from Wyoming DOT (WYDOT), Tampa Hillsborough Expressway Authority (THEA), and New York City DOT (NYCDOT). The following sections provide a brief summary of the data files in their various historical schemas. Each data file contains one sample record.

### WYDOT Samples
#### Basic Safety Message (BSM) Files
- wydot-filtered-bsm-schemaVersion3.json
- wydot-filtered-bsm-schemaVersion5.json
- wydot-filtered-bsm-schemaVersion6.json

#### Traveler Information Message (TIM) Files
 - wydot-filtered-tim-schemaVersion3.json
 - wydot-filtered-tim-schemaVersion5.json
 - wydot-filtered-tim-schemaVersion6_multi.json
   - This file contains TIM data where array elements contain multiple elements. Such arrays are represented in the schema as JSON arrays.
 - wydot-filtered-tim-schemaVersion6_single.json
   - This file contains TIM data where array elements contain a single element. Such single-element arrays are represented as a single JSON object/dictionary.

### THEA Samples
#### Basic Safety Message (BSM) Files
- thea-filtered-bsm-schemaVersion1.json

#### Traveler Information Message (TIM) Files
- thea-filtered-tim-schemaVersion1.json

#### Signal Phasing and Timing (SPaT) Files
- thea-filtered-spat-schemaVersion1.json

### NYCDOT Samples
#### Event Log Samples
- nycdot-cspdomp-event.json
- nycdot-evacinfo-event.json
- nycdot-fcw-event.json
- nycdot-ima-event.json
- nycdot-ovcclearancelimit-event.json
- nycdot-spdcomp-event.json


## Work Zone Data Exchange (WZDx) Archive
ITS DataHub archives snapshots of WZDx-compliant live work zone feeds that are registered with the [Work Zone Feed Registry](https://data.transportation.gov/d/69qe-yiui). Since the WZDx specification updates every 6 months or so, please refer to the [WZDx specification GitHub repository](https://github.com/usdot-jpo-ode/wzdx) for sample files.