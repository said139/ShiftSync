import os
import random
import re
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_RAW = os.path.join(DATA_DIR, "shiftsync_handover_nlp_dataset.csv")
OUTPUT_DEDUP = os.path.join(DATA_DIR, "shiftsync_handover_nlp_dataset_deduplicated.csv")

# Set fixed seed for reproducibility
random.seed(42)
np.random.seed(42)

SHIFTS = [
    "Morning Flight Ops & Line Maint A",
    "Night Turnaround & Defect Rectification B",
    "Transit Ramp Check Shift C",
    "Emergency AOG Standby Shift"
]

INDUSTRIES = [
    "Flight Operations (Cockpit & Pilots)",
    "Aeronautical Line Maintenance",
    "Avionics & Flight Control Systems",
    "Airframe & Powerplant Engineering",
    "Fleet Airworthiness & CAMO Compliance"
]

# Curated Aviation Task Corpora (Spanning Pilots & Aeronautical Engineers)
AVIATION_TASKS = [
    # =========================================================================
    # 1. EQUIPMENT CHECK (Pre-flight, Line Checks, Avionics, Powerplant, Hydraulics)
    # =========================================================================
    {
        "desc": "Checked Boeing 787 left engine oil and pressure sensor readings; parameter stable within flight envelope.",
        "cat": "Equipment Check", "prio": "High", "stat": "Completed",
        "ind": "Airframe & Powerplant Engineering",
        "action": "Verify parameter trends against engine monitoring telemetry before next sector dispatch."
    },
    {
        "desc": "Inspect boiler pressure valve on Line 2 after fluctuating readings between 75 and 92 PSI throughout afternoon run.",
        "cat": "Equipment Check", "prio": "High", "stat": "Pending",
        "ind": "Aeronautical Line Maintenance",
        "action": "Perform detailed physical inspection within first 30 minutes of shift, log baseline values in ShiftSync."
    },
    {
        "desc": "Verified auxiliary power unit APU generator output stable at 115V AC and 400Hz frequency under electrical load.",
        "cat": "Equipment Check", "prio": "Medium", "stat": "Completed",
        "ind": "Avionics & Flight Control Systems",
        "action": "Log APU voltage baseline and generator frequency into electronic maintenance ledger."
    },
    {
        "desc": "Performed pre-flight cockpit instrument scan, EFIS glass display test, and master caution warning check on 5Y-KZE.",
        "cat": "Equipment Check", "prio": "Medium", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "Complete standard pre-flight flight deck checklist and verify instrument alignment."
    },
    {
        "desc": "Checked main landing gear brake wear indicator pins and hydraulic accumulator pre-charge at 3000 PSI nominal.",
        "cat": "Equipment Check", "prio": "High", "stat": "In Progress",
        "ind": "Aeronautical Line Maintenance",
        "action": "Record pin protrusion millimeters and recharge nitrogen accumulator if pressure drops below 2850 PSI."
    },
    {
        "desc": "Calibrate pitot-static probe heating elements and angle-of-attack vane transducers prior to night departure.",
        "cat": "Equipment Check", "prio": "Medium", "stat": "Pending",
        "ind": "Avionics & Flight Control Systems",
        "action": "Measure heating element resistance ohms and verify de-icing current draw on ground test."
    },
    {
        "desc": "Tested weather radar transceiver and TCAS II collision avoidance antenna system; built-in self-test passed.",
        "cat": "Equipment Check", "prio": "Medium", "stat": "Completed",
        "ind": "Avionics & Flight Control Systems",
        "action": "Confirm weather radar sweep range and verify TCAS audio warning annunciator."
    },
    {
        "desc": "Monitored engine fuel differential pressure bypass indicator on Engine 2; green normal band verified.",
        "cat": "Equipment Check", "prio": "High", "stat": "Completed",
        "ind": "Airframe & Powerplant Engineering",
        "action": "Inspect fuel filter pop-out indicator button and document in transit inspection checklist."
    },
    {
        "desc": "Inspected emergency emergency locator transmitter ELT beacon and cockpit audio voice recorder test.",
        "cat": "Equipment Check", "prio": "High", "stat": "Completed",
        "ind": "Avionics & Flight Control Systems",
        "action": "Verify ELT battery expiration date stamp and log CVR test tone verification."
    },
    {
        "desc": "Check bleed air pre-cooler duct temperature and pressure regulating shutoff valves during engine ground idle.",
        "cat": "Equipment Check", "prio": "High", "stat": "Pending",
        "ind": "Airframe & Powerplant Engineering",
        "action": "Cross-check EICAS pneumatic duct pressure readings across left and right packs."
    },
    {
        "desc": "Zero-point calibration on nose wheel steering tiller feedback transducer completed by avionics engineer.",
        "cat": "Equipment Check", "prio": "Medium", "stat": "Completed",
        "ind": "Avionics & Flight Control Systems",
        "action": "Perform ground rudder pedal steering deflection test and confirm zero degree tracking."
    },
    {
        "desc": "Inspected ram air turbine RAT deployment latch mechanism and heater probe resistance on Boeing 787-8.",
        "cat": "Equipment Check", "prio": "High", "stat": "Completed",
        "ind": "Airframe & Powerplant Engineering",
        "action": "Verify RAT safety ground lock pin is engaged during hangar maintenance."
    },
    {
        "desc": "Scanned flight management computer FMC navigation database revision cycle for expiration on Embraer E190.",
        "cat": "Equipment Check", "prio": "Low", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "Confirm current AIRAC navigation database cycle active across both FMC units."
    },
    {
        "desc": "Check tire pressure and tread depth on all 8 main gear tires and 2 nose gear tires before afternoon rotation.",
        "cat": "Equipment Check", "prio": "Medium", "stat": "Pending",
        "ind": "Aeronautical Line Maintenance",
        "action": "Ensure main gear pressures exceed 205 PSI and nose gear exceeds 190 PSI; record in tire log."
    },
    {
        "desc": "Verified standby altimeter calibration against barometric field elevation at JKIA Runway 06.",
        "cat": "Equipment Check", "prio": "Medium", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "Confirm standby altimeter reading within plus or minus 20 feet of field elevation."
    },

    # =========================================================================
    # 2. MAINTENANCE (Snag Rectification, Parts Swaps, Rigging, Repairs, Overhauls)
    # =========================================================================
    {
        "desc": "Replaced faulty sensor and worn conveyor belt bearing in packaging area.",
        "cat": "Maintenance", "prio": "High", "stat": "Completed",
        "ind": "Aeronautical Line Maintenance",
        "action": "Supervise replacement at scheduled window, verify vibration thresholds post-repair."
    },
    {
        "desc": "Rectified TechLog snag #4412: replaced faulty line replaceable unit LRU for VHF Comm transceiver #1.",
        "cat": "Maintenance", "prio": "High", "stat": "Completed",
        "ind": "Avionics & Flight Control Systems",
        "action": "Perform VHF radio ground transmission check with JKIA Tower on 118.1 MHz and clear TechLog."
    },
    {
        "desc": "Replaced leaking hydraulic return line B-nut seal on left main landing gear bay; leak check negative at 3000 PSI.",
        "cat": "Maintenance", "prio": "High", "stat": "Completed",
        "ind": "Airframe & Powerplant Engineering",
        "action": "Torque B-nut fitting to specified aircraft maintenance manual limits and safety wire."
    },
    {
        "desc": "Replaced worn elevator trim tab mechanical actuator; free play adjusted within manufacturer tolerances.",
        "cat": "Maintenance", "prio": "High", "stat": "Completed",
        "ind": "Airframe & Powerplant Engineering",
        "action": "Conduct dual inspection flight control sign-off and complete duplicate inspection certificate."
    },
    {
        "desc": "Main hydraulic line ruptured on Air Compressor AC-04 causing immediate line halt. Oil contained, replacement hose arriving.",
        "cat": "Maintenance", "prio": "Critical", "stat": "In Progress",
        "ind": "Aeronautical Line Maintenance",
        "action": "Continuous monitoring of repair progress, ensure standby units ready, expedite technician parts dispatch."
    },
    {
        "desc": "Cleared EICAS fault code #ENG-342: replaced dirty fuel bypass differential pressure filter element on Engine 2.",
        "cat": "Maintenance", "prio": "High", "stat": "Completed",
        "ind": "Airframe & Powerplant Engineering",
        "action": "Perform static engine idle ground run, check for fuel leaks, and update maintenance control."
    },
    {
        "desc": "Lubricated trailing edge flap tracks and leading edge slats per scheduled 500-flight-hour maintenance card.",
        "cat": "Maintenance", "prio": "Medium", "stat": "Completed",
        "ind": "Aeronautical Line Maintenance",
        "action": "Wipe excess grease and confirm flap mechanism extension and retraction cycle smooth."
    },
    {
        "desc": "Rectified cabin pressurization outflow valve hunting by cleaning valve throat and recalibrating stepper motor.",
        "cat": "Maintenance", "prio": "High", "stat": "In Progress",
        "ind": "Airframe & Powerplant Engineering",
        "action": "Run cabin pressurization ground leak test and record pressure decay rate over 10 minutes."
    },
    {
        "desc": "Replaced failed cockpit windshield wiper motor on captain side prior to scheduled flight KQ 102 departure.",
        "cat": "Maintenance", "prio": "High", "stat": "Completed",
        "ind": "Aeronautical Line Maintenance",
        "action": "Perform rain repellent and wiper speed sweep test on Captain windshield."
    },
    {
        "desc": "Repaired chafed wiring bundle near avionics bay rack E3; insulation resistance test verified nominal.",
        "cat": "Maintenance", "prio": "High", "stat": "Completed",
        "ind": "Avionics & Flight Control Systems",
        "action": "Install silicone abrasion sleeve and secure harness with aviation grade lacing tape."
    },
    {
        "desc": "Swapped unserviceable landing gear anti-skid control transducer on wheel #3 following pilot brake shudder report.",
        "cat": "Maintenance", "prio": "High", "stat": "Completed",
        "ind": "Aeronautical Line Maintenance",
        "action": "Execute anti-skid BIT test and confirm all wheel speed sensors reporting zero error codes."
    },
    {
        "desc": "Overhauled nose landing gear taxi light assembly and replaced blown high-intensity LED harness.",
        "cat": "Maintenance", "prio": "Medium", "stat": "Completed",
        "ind": "Avionics & Flight Control Systems",
        "action": "Verify taxi and turnoff illumination alignment and sign off electrical task card."
    },
    {
        "desc": "Adjusted thrust lever resolver angle TLA rigging on Engine 1 throttle quadrant per TechLog discrepancy.",
        "cat": "Maintenance", "prio": "High", "stat": "In Progress",
        "ind": "Airframe & Powerplant Engineering",
        "action": "Calibrate engine electronic controller FADEC resolver angles at idle and max takeoff positions."
    },
    {
        "desc": "Replaced depleted fire extinguisher squib cartridge in APU compartment and tested fire detection loop.",
        "cat": "Maintenance", "prio": "Critical", "stat": "Completed",
        "ind": "Airframe & Powerplant Engineering",
        "action": "Verify continuity of squib firing circuit and tag expired cartridge for disposal."
    },
    {
        "desc": "Main cooling water pump P-45 bearing seized, causing engine overheating. Replacement pump offline; rebuilding motor.",
        "cat": "Maintenance", "prio": "Critical", "stat": "In Progress",
        "ind": "Aeronautical Line Maintenance",
        "action": "Continuous monitoring of repair progress, ensure standby units ready, expedite technician dispatch."
    },

    # =========================================================================
    # 3. SAFETY & COMPLIANCE (Airworthiness Directives, Grounding, CRS, FOD, O2)
    # =========================================================================
    {
        "desc": "Major chemical spill reported in Warehouse Sector B, evacuated personnel.",
        "cat": "Safety & Compliance", "prio": "Critical", "stat": "Pending",
        "ind": "Fleet Airworthiness & CAMO Compliance",
        "action": "Immediate escalation to safety supervisor, ensure area remains isolated, await hazardous response team."
    },
    {
        "desc": "Signed off Kenya Civil Aviation Authority KCAA Certificate of Release to Service CRS following A-check completion.",
        "cat": "Safety & Compliance", "prio": "Critical", "stat": "Completed",
        "ind": "Fleet Airworthiness & CAMO Compliance",
        "action": "File CRS original copy in aircraft technical records and upload digital scan to CAMO portal."
    },
    {
        "desc": "Critical AOG grounding: micro-fracture discovered on titanium fan blade root during borescope inspection.",
        "cat": "Safety & Compliance", "prio": "Critical", "stat": "Pending",
        "ind": "Fleet Airworthiness & CAMO Compliance",
        "action": "Immediately revoke release to service, place red AOG tag on aircraft, alert Chief Engineer."
    },
    {
        "desc": "Structural crack observed on support beam near HVAC Plant Deck. Immediate structural engineering inspection ordered; access restricted.",
        "cat": "Safety & Compliance", "prio": "Critical", "stat": "Pending",
        "ind": "Airframe & Powerplant Engineering",
        "action": "Immediate escalation to safety supervisor, ensure area remains isolated, await engineering inspection."
    },
    {
        "desc": "Major safety alert: jet fuel seepage detected at engine pylon fuel disconnect coupling; aircraft grounded pending seal swap.",
        "cat": "Safety & Compliance", "prio": "Critical", "stat": "Pending",
        "ind": "Fleet Airworthiness & CAMO Compliance",
        "action": "Position fire extinguishers on ramp, ground aircraft electrical power, and notify fire rescue."
    },
    {
        "desc": "Conducted mandatory foreign object debris FOD inspection on JKIA Terminal 1A Gate 4 ramp sector; zero debris confirmed.",
        "cat": "Safety & Compliance", "prio": "High", "stat": "Completed",
        "ind": "Aeronautical Line Maintenance",
        "action": "Log ramp sector FOD clearance status in aerodrome ground operations safety ledger."
    },
    {
        "desc": "Inspected cabin and flight deck emergency oxygen cylinders; verified pressure at 1850 PSI nominal.",
        "cat": "Safety & Compliance", "prio": "High", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "Confirm oxygen bottle shutoff valve wire-locked in open position and record gauge pressure."
    },
    {
        "desc": "Performed operational functional check of engine and APU fire extinguishing squib circuits; all bottles armed and verified.",
        "cat": "Safety & Compliance", "prio": "Critical", "stat": "Completed",
        "ind": "Avionics & Flight Control Systems",
        "action": "Verify fire bottle squib continuity resistance is between 1.5 and 2.5 ohms."
    },
    {
        "desc": "Investigated pilot-reported bird strike on right wing leading edge slat #3; composite ultrasonic NDT inspection completed.",
        "cat": "Safety & Compliance", "prio": "Critical", "stat": "Completed",
        "ind": "Fleet Airworthiness & CAMO Compliance",
        "action": "Verify no structural delamination or rib damage; sign off bird strike inspection report."
    },
    {
        "desc": "Audited pilot flight and duty time limitations FTL and rest period compliance ahead of long-haul sector KQ 102.",
        "cat": "Safety & Compliance", "prio": "High", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "Confirm captain and first officer flight duty hours comply strictly with KCAA safety regulations."
    },
    {
        "desc": "Completed mandatory pre-shift gas testing for oxygen deficiency and LEL in confined space tank #5. Safe to enter.",
        "cat": "Safety & Compliance", "prio": "High", "stat": "Completed",
        "ind": "Aeronautical Line Maintenance",
        "action": "Audit verification log, ensure all corrective action items signed off by HSE officer."
    },
    {
        "desc": "Verified minimum equipment list MEL time expiry for Cat B and Cat C deferred maintenance snags.",
        "cat": "Safety & Compliance", "prio": "High", "stat": "Completed",
        "ind": "Fleet Airworthiness & CAMO Compliance",
        "action": "Cross-check MEL tracking board against flight dispatch schedule to avoid operating past expiry."
    },
    {
        "desc": "Verified emergency evacuation slide girt bar engagement and cabin door arming mechanisms on all exit doors.",
        "cat": "Safety & Compliance", "prio": "High", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "Ensure slide pressure indicators in green arc and door emergency power assist bottles charged."
    },
    {
        "desc": "Conducted emergency fuel spill response drill with incoming and outgoing crew in hangar apron. Log submitted to Safety Officer.",
        "cat": "Safety & Compliance", "prio": "High", "stat": "Completed",
        "ind": "Fleet Airworthiness & CAMO Compliance",
        "action": "Audit verification log, ensure all corrective action items signed off by HSE officer."
    },
    {
        "desc": "Inspected fire extinguishers and emergency exit signs across Sector Gamma; replaced 2 expired units in corridor B.",
        "cat": "Safety & Compliance", "prio": "High", "stat": "Completed",
        "ind": "Aeronautical Line Maintenance",
        "action": "Audit verification log, ensure all corrective action items signed off by HSE officer."
    },

    # =========================================================================
    # 4. OPERATIONS (Flight Dispatch, Fuel Uplift, Turnaround, Pushback, Briefings)
    # =========================================================================
    {
        "desc": "Verified final flight plan fuel uplift of 42600 kg and cross-checked fuel density against fueler delivery docket.",
        "cat": "Operations", "prio": "Medium", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "Cross-check fuel gauge quantity against fuel delivery ticket and compute total onboard discrepancy."
    },
    {
        "desc": "Calculated aircraft takeoff weight, CG trim, and V-speeds V1 Vr V2 for runway 06 departure on Boeing 787.",
        "cat": "Operations", "prio": "Medium", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "Verify trim setting dialed onto stabilizer trim wheel and cross-check with First Officer."
    },
    {
        "desc": "Handed over flight dispatch operational release and NOTAM weather briefing pack to incoming flight crew.",
        "cat": "Operations", "prio": "Medium", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "Brief oncoming crew regarding enroute turbulence, alternate airport weather, and active NOTAMs."
    },
    {
        "desc": "Coordinated pushback tractor clearance and ground communication headset interphone link for flight KQ 102 to London.",
        "cat": "Operations", "prio": "Medium", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "Verify steering bypass pin removed and shown to flight deck before taxi clearance."
    },
    {
        "desc": "Debriefed transit turnaround ground time: passenger deplaning, baggage offload, and catering completed in 42 minutes.",
        "cat": "Operations", "prio": "Medium", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "Ensure on-time turnaround metrics recorded in station flight operations log."
    },
    {
        "desc": "Verified de-icing fluid Type IV holdover time computation ahead of cold-weather European sector arrival.",
        "cat": "Operations", "prio": "High", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "Record anti-icing application start time and confirm precipitation holdover limits."
    },
    {
        "desc": "Reconciled passenger load manifest with electronic flight bag EFB performance database before door closure.",
        "cat": "Operations", "prio": "Medium", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "Confirm zero passenger count discrepancy between boarding gate scanners and cabin purser."
    },
    {
        "desc": "Dispatched scheduled air cargo freight container ULD positions according to aircraft balance envelope.",
        "cat": "Operations", "prio": "Medium", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "Confirm cargo compartment tie-down locks engaged and gross zero fuel weight verified."
    },
    {
        "desc": "Swept and mopped gangways in packing hall H-B at conclusion of packaging run.",
        "cat": "Operations", "prio": "Low", "stat": "Completed",
        "ind": "Aeronautical Line Maintenance",
        "action": "Routine handover sign-off, verify area cleanliness and equipment shutdown."
    },
    {
        "desc": "Offloaded 4 container trailers at loading bay 4. Received bill of lading and entered records into WMS.",
        "cat": "Operations", "prio": "Medium", "stat": "Completed",
        "ind": "Aeronautical Line Maintenance",
        "action": "Continue production throughput tracking, ensure target quotas met before next handover."
    },
    {
        "desc": "Coordinated ground power unit GPU connection and pre-conditioned air duct coupling at Gate 3 for aircraft arrival.",
        "cat": "Operations", "prio": "Medium", "stat": "Completed",
        "ind": "Aeronautical Line Maintenance",
        "action": "Verify ground power phase sequence and voltage prior to connecting to aircraft bus."
    },
    {
        "desc": "Performed flight crew pre-flight cockpit handover briefing covering enroute weather, winds, and alternate airports.",
        "cat": "Operations", "prio": "Medium", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "Review oceanic crossing altitude clearance and communication selcal check."
    },

    # =========================================================================
    # 5. ADMINISTRATION (TechLog Archiving, MEL Logging, Voyage Reports, Work Orders)
    # =========================================================================
    {
        "desc": "Updated shift logbook Section 4 and filed maintenance work orders.",
        "cat": "Administration", "prio": "Low", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "File documentation into record repository, confirm routine sign-off."
    },
    {
        "desc": "Closed and archived Aircraft Technical Logbook TechLog page #4412 in airline MRO enterprise system.",
        "cat": "Administration", "prio": "Low", "stat": "Completed",
        "ind": "Fleet Airworthiness & CAMO Compliance",
        "action": "Ensure pink and yellow copies distributed per standard operating procedure."
    },
    {
        "desc": "Recorded Minimum Equipment List MEL deferral Cat C #21-31-01 for cabin recirculation fan with Chief Engineer sign-off.",
        "cat": "Administration", "prio": "Low", "stat": "Completed",
        "ind": "Fleet Airworthiness & CAMO Compliance",
        "action": "Place MEL cockpit placard on instrument panel and set calendar countdown alert for 10-day rectification limit."
    },
    {
        "desc": "Filed pilot voyage report and flight defect debrief logs with Flight Operations JKIA dispatch.",
        "cat": "Administration", "prio": "Low", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "Archive electronic flight deck voyage log into operational database."
    },
    {
        "desc": "Updated aircraft maintenance tracking software with engine cyclic flight hours and landing cycles.",
        "cat": "Administration", "prio": "Low", "stat": "Completed",
        "ind": "Fleet Airworthiness & CAMO Compliance",
        "action": "Synchronize ACARS flight cycle telemetry with engine manufacturer maintenance database."
    },
    {
        "desc": "Submitted line maintenance shift handover checklist to CAMO quality assurance department.",
        "cat": "Administration", "prio": "Low", "stat": "Completed",
        "ind": "Aeronautical Line Maintenance",
        "action": "Upload completed digital shift report with engineer sign-offs to quality intranet."
    },
    {
        "desc": "Print updated SOP revision 4.2 for hazardous material handling and clip to shift notice board.",
        "cat": "Administration", "prio": "Low", "stat": "Pending",
        "ind": "Fleet Airworthiness & CAMO Compliance",
        "action": "File documentation into record repository, confirm routine sign-off."
    },
    {
        "desc": "Logged aircraft component serial numbers and rotables return docket into maintenance stores inventory.",
        "cat": "Administration", "prio": "Low", "stat": "Completed",
        "ind": "Aeronautical Line Maintenance",
        "action": "Affix serviceable tag or unserviceable red repair tag to removed aircraft LRU component."
    },
    {
        "desc": "Handed over master locker keys and radio communication sets to incoming shift lead in briefing room.",
        "cat": "Administration", "prio": "Low", "stat": "Completed",
        "ind": "Flight Operations (Cockpit & Pilots)",
        "action": "File documentation into record repository, confirm routine sign-off."
    },
    {
        "desc": "Archived daily SCADA telemetry logs and backed up operational reports to secure cloud drive.",
        "cat": "Administration", "prio": "Low", "stat": "Completed",
        "ind": "Fleet Airworthiness & CAMO Compliance",
        "action": "File documentation into record repository, confirm routine sign-off."
    },
    {
        "desc": "Updated whiteboard task allocation chart for tomorrow's scheduled maintenance outage.",
        "cat": "Administration", "prio": "Low", "stat": "Pending",
        "ind": "Aeronautical Line Maintenance",
        "action": "File documentation into record repository, confirm routine sign-off."
    }
]

# Generate programmatic parametric variations to expand corpus to 1,200 samples with zero label contradiction
AIRCRAFT_TAILS = ["5Y-KZE (B787)", "5Y-KZB (B787)", "5Y-FFF (E190)", "5Y-KYR (E190)", "5Y-CYA (B737)", "5Y-BBA (Q400)"]
ENGINES = ["Trent 1000 Engine #1", "Trent 1000 Engine #2", "GE CF34 Left Engine", "GE CF34 Right Engine", "APU GTCP331"]
GATES = ["Gate 4", "Gate 12", "Gate 1A", "Gate 2B", "Hangar 1", "Hangar 2 Apron", "Ramp Sector 1", "Ramp Sector 2"]
SECTORS = ["KQ 102 to London", "KQ 504 to Entebbe", "KQ 310 to Dubai", "KQ 412 to Johannesburg", "KQ 606 to Mombasa"]

VARIATION_TEMPLATES = [
    # Equipment Check
    ("Inspected {engine} oil pressure and vibration sensor telemetry; verified within flight envelope limits on {tail}.", "Equipment Check", "High", "In Progress", "Airframe & Powerplant Engineering", "Verify baseline telemetry trends in electronic maintenance ledger."),
    ("Checked hydraulic system {hyd} accumulator pressure and reservoir fluid level at {gate}; reading steady at 3000 PSI.", "Equipment Check", "Medium", "Completed", "Aeronautical Line Maintenance", "Log baseline hydraulic accumulator pressure in transit inspection report."),
    ("Scanned glass cockpit primary flight display PFD and navigation display ND on {tail}; zero system failure flags.", "Equipment Check", "Medium", "Completed", "Flight Operations (Cockpit & Pilots)", "Verify cockpit display brightness and instrument cross-comparison."),
    ("Check tire pressure and brake wear indicator pins on {tail} at {gate} before scheduled departure on {sector}.", "Equipment Check", "Medium", "Pending", "Aeronautical Line Maintenance", "Measure wear pins and verify tire pressures exceed minimum dispatch limits."),
    ("Tested weather radar transceiver and TCAS II self-test pass on {tail}; audio annunciator loud and clear.", "Equipment Check", "Medium", "Completed", "Avionics & Flight Control Systems", "Verify radar antenna tilt calibration and TCAS traffic display."),
    ("Calibrated angle of attack sensor vane and pitot-static heating circuit on {tail} prior to turnaround departure.", "Equipment Check", "Medium", "Completed", "Avionics & Flight Control Systems", "Measure heater resistance and verify zero error codes on avionics display."),
    ("Checked flight deck emergency oxygen mask flow regulators and cylinder pressure on {tail}; 1850 PSI nominal.", "Equipment Check", "High", "Completed", "Flight Operations (Cockpit & Pilots)", "Verify oxygen mask microphone and emergency dilution selector."),

    # Maintenance
    ("Replaced faulty {lru} line replaceable unit on {tail} per TechLog discrepancy; functional test passed.", "Maintenance", "High", "Completed", "Avionics & Flight Control Systems", "Complete aircraft maintenance manual functional test and clear TechLog entry."),
    ("Cleared EICAS alert message #ENG-{code}: replaced dirty fuel differential pressure filter on {engine}.", "Maintenance", "High", "Completed", "Airframe & Powerplant Engineering", "Perform engine ground idle run, check for leaks, and sign off task card."),
    ("Replaced leaking hydraulic return B-nut seal on {tail} landing gear bay at {gate}; leak check nominal at 3000 PSI.", "Maintenance", "High", "Completed", "Airframe & Powerplant Engineering", "Torque fitting to AMM specifications and install fresh safety lockwire."),
    ("Overhauled elevator trim tab actuator and adjusted mechanical control cable tension on {tail}.", "Maintenance", "High", "Completed", "Airframe & Powerplant Engineering", "Conduct duplicate inspection of primary flight control connection."),
    ("Swapped unserviceable landing gear anti-skid transducer on {tail} following pilot brake chatter defect report.", "Maintenance", "High", "Completed", "Aeronautical Line Maintenance", "Verify anti-skid BIT pass and check wheel speed sensor connector pins."),
    ("Lubricated trailing edge flap tracks and leading edge slats on {tail} per scheduled transit maintenance card.", "Maintenance", "Medium", "Completed", "Aeronautical Line Maintenance", "Wipe excess grease and confirm flap extension mechanism operates smoothly."),
    ("Repaired chafed avionics wire bundle near electrical distribution panel P6 on {tail}; insulation test verified.", "Maintenance", "High", "Completed", "Avionics & Flight Control Systems", "Apply heat shrink insulation sleeve and secure harness with clamps."),

    # Safety & Compliance
    ("Signed off Certificate of Release to Service CRS for {tail} following defect rectification on {sector}.", "Safety & Compliance", "Critical", "Completed", "Fleet Airworthiness & CAMO Compliance", "Transmit CRS digital copy to flight dispatch and archive physical certificate."),
    ("Critical AOG grounding: micro-crack detected on {engine} compressor blade root during borescope check on {tail}.", "Safety & Compliance", "Critical", "Pending", "Fleet Airworthiness & CAMO Compliance", "Apply red AOG tag, ground aircraft, and notify maintenance control immediately."),
    ("Major safety alert: jet fuel leak detected near engine pylon on {tail} at {gate}; aircraft grounded for seal swap.", "Safety & Compliance", "Critical", "Pending", "Fleet Airworthiness & CAMO Compliance", "Position ramp fire extinguishers and isolate electrical power immediately."),
    ("Conducted mandatory foreign object debris FOD sweep on ramp at {gate}; runway and taxiway verified clear.", "Safety & Compliance", "High", "Completed", "Aeronautical Line Maintenance", "Document FOD inspection time and sign off aerodrome safety ledger."),
    ("Investigated pilot-reported bird strike on wing leading edge on {tail}; ultrasonic NDT inspection completed nominal.", "Safety & Compliance", "Critical", "Completed", "Fleet Airworthiness & CAMO Compliance", "Confirm zero composite delamination and sign off structural inspection."),
    ("Audited flight deck crew flight duty time limitations FTL ahead of long-haul departure on {sector}.", "Safety & Compliance", "High", "Completed", "Flight Operations (Cockpit & Pilots)", "Confirm pilot legal rest compliance with civil aviation safety authority."),
    ("Verified emergency evacuation slide pack arming mechanisms and girt bars on all doors of {tail}.", "Safety & Compliance", "High", "Completed", "Flight Operations (Cockpit & Pilots)", "Verify slide inflation bottle pressure indicators in green operational arc."),

    # Operations
    ("Verified flight plan fuel uplift calculation of {fuel} kg on {tail} for flight {sector}; density verified.", "Operations", "Medium", "Completed", "Flight Operations (Cockpit & Pilots)", "Cross-check cockpit fuel totalizer against delivery receipt and compute uplift."),
    ("Calculated aircraft takeoff gross weight, stabilizer trim, and V-speeds for runway departure on {sector}.", "Operations", "Medium", "Completed", "Flight Operations (Cockpit & Pilots)", "Verify stabilizer trim units set on center pedestal and cross-check with crew."),
    ("Handed over flight dispatch briefing pack, weather satellite imagery, and active NOTAMs for flight {sector}.", "Operations", "Medium", "Completed", "Flight Operations (Cockpit & Pilots)", "Brief flight deck relief crew regarding enroute SIGMETs and alternates."),
    ("Coordinated pushback tug clearance, ground interphone link, and steering lockout pin verification for {sector}.", "Operations", "Medium", "Completed", "Flight Operations (Cockpit & Pilots)", "Confirm ground crew shows steering bypass pin before aircraft taxi-out."),
    ("Completed scheduled passenger deplaning, cabin cleaning, and ground turnaround for {tail} at {gate} in 38 minutes.", "Operations", "Medium", "Completed", "Flight Operations (Cockpit & Pilots)", "Record on-time transit turnaround performance in station logbook."),
    ("Reconciled electronic flight bag EFB passenger load manifest with final boarding gate tally on {sector}.", "Operations", "Medium", "Completed", "Flight Operations (Cockpit & Pilots)", "Confirm final passenger count matches dispatch release before main door arming."),

    # Administration
    ("Closed and archived Aircraft Technical Logbook TechLog page #{log_num} for {tail} into MRO enterprise ledger.", "Administration", "Low", "Completed", "Fleet Airworthiness & CAMO Compliance", "File original TechLog copy and upload digital record to maintenance database."),
    ("Recorded Minimum Equipment List MEL deferral Cat C for secondary subsystem on {tail} with Chief Engineer approval.", "Administration", "Low", "Completed", "Fleet Airworthiness & CAMO Compliance", "Affix MEL cockpit placard and set automated countdown in maintenance tracking."),
    ("Filed pilot voyage report and flight debrief logbook with Flight Operations JKIA dispatch for {sector}.", "Administration", "Low", "Completed", "Flight Operations (Cockpit & Pilots)", "Archive captain voyage debrief notes into airline flight safety records."),
    ("Updated aircraft fleet maintenance tracking system with engine flight hours and flight cycles for {tail}.", "Administration", "Low", "Completed", "Fleet Airworthiness & CAMO Compliance", "Synchronize ACARS telemetry logs with central engine health monitoring."),
    ("Submitted line maintenance shift turnover documentation to CAMO quality assurance department.", "Administration", "Low", "Completed", "Aeronautical Line Maintenance", "Ensure all outgoing and incoming engineer digital signatures are attached."),
    ("Logged removed rotable component serial numbers and unserviceable repair tags into maintenance stores.", "Administration", "Low", "Completed", "Aeronautical Line Maintenance", "Attach unserviceable parts tag and coordinate logistics shipping to overhaul shop.")
]

def build_dataset():
    records = []
    
    # 1. Add all core hand-crafted tasks
    for item in AVIATION_TASKS:
        records.append({
            "shift_type": random.choice(SHIFTS),
            "industry": item["ind"],
            "task_description": item["desc"],
            "category": item["cat"],
            "priority": item["prio"],
            "status": item["stat"],
            "suggested_action": item["action"]
        })

    # 2. Expand with realistic parametric variations
    LRUS = ["VHF Comm Transceiver", "Flight Management Computer FMC", "VOR Navigation Receiver", "TCAS Computer", "ADIRU Air Data Unit", "Autothrottle Servo", "Static Inverter"]
    HYD_SYSTEMS = ["System A", "System B", "Left System", "Right System", "Center System"]
    
    idx = 0
    while len(records) < 1200:
        tmpl, cat, prio, stat, ind, action = VARIATION_TEMPLATES[idx % len(VARIATION_TEMPLATES)]
        idx += 1
        
        tail = random.choice(AIRCRAFT_TAILS)
        engine = random.choice(ENGINES)
        gate = random.choice(GATES)
        sector = random.choice(SECTORS)
        lru = random.choice(LRUS)
        hyd = random.choice(HYD_SYSTEMS)
        fuel = str(random.randint(18, 55) * 1000)
        code = str(random.randint(210, 890))
        log_num = str(random.randint(4100, 4899))
        
        text = tmpl.format(tail=tail, engine=engine, gate=gate, sector=sector, lru=lru, hyd=hyd, fuel=fuel, code=code, log_num=log_num)
        
        records.append({
            "shift_type": random.choice(SHIFTS),
            "industry": ind,
            "task_description": text,
            "category": cat,
            "priority": prio,
            "status": stat,
            "suggested_action": action
        })

    # Create DataFrame
    df = pd.DataFrame(records[:1200])
    df["task_id"] = [f"TSK-AV-{1001 + i}" for i in range(len(df))]
    
    # Reorder columns
    cols = ["task_id", "shift_type", "industry", "task_description", "category", "priority", "status", "suggested_action"]
    df = df[cols]
    
    # Save Raw Dataset
    df.to_csv(OUTPUT_RAW, index=False)
    print(f"Aviation Raw Dataset generated ({len(df)} records) -> {OUTPUT_RAW}")

    # Generate Clean Deduplicated Benchmark Dataset
    df_dedup = df.drop_duplicates(subset=["task_description"]).copy()
    df_dedup["task_id"] = [f"TSK-U-{1001 + i}" for i in range(len(df_dedup))]
    df_dedup.to_csv(OUTPUT_DEDUP, index=False)
    print(f"Aviation Deduplicated Dataset generated ({len(df_dedup)} records) -> {OUTPUT_DEDUP}")

    print("\n--- Class Distribution (Deduplicated) ---")
    print("Categories:\n", df_dedup["category"].value_counts())
    print("\nPriorities:\n", df_dedup["priority"].value_counts())
    print("\nIndustries:\n", df_dedup["industry"].value_counts())

if __name__ == "__main__":
    build_dataset()
