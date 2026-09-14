from typing import List, Dict, Any

PRESET_LOCATIONS: List[Dict[str, Any]] = [
    {
        "id": "mankapur",
        "name": "Mankapur Sports Complex, Nagpur",
        "subtitle": "North Ward X — Mankapur Sports Complex & Indoor Stadium Corridor",
        "colorDiff": 12.40,
        "ssimArea": 15.80,
        "status": "flagged",
        "statusLabel": "Divergent / Flagged",
        "coords": "79.060° E, 21.170° N → 79.100° E, 21.210° N",
        "coordinates": [21.1900, 79.0800],
        "ssimScore": 0.6050,
        "confidence": "cross_confirmed",
        "confidenceLabel": "Cross-Resolution Confirmed",
        "permits": [
            {"id": "NMC-SPORTS-2023-4011", "plot": "Mankapur Indoor Stadium Expansion", "status": "matched", "date": "22 May 2023"},
            {"id": "UNSANCTIONED-mank-1", "plot": "North Sports Ground Encroachment", "status": "unmatched", "date": "No Record"}
        ],
        "polygons": [
            {
                "polygon_id": "POLY-MANK-001",
                "area_m2": 24200.0,
                "coordinates": [
                    [21.1885, 79.0780],
                    [21.1915, 79.0780],
                    [21.1915, 79.0820],
                    [21.1885, 79.0820]
                ]
            }
        ],
        "tiers": {
            "10m": {
                "source": "Sentinel-2 (Live Copernicus CDSE)",
                "beforeImage": "/static/results/mankapur_sports_complex__nagpur_20220222_20250226_c8e72f3a/before.png",
                "afterImage": "/static/results/mankapur_sports_complex__nagpur_20220222_20250226_c8e72f3a/after.png",
                "colorDiffOverlay": "/static/results/mankapur_sports_complex__nagpur_20220222_20250226_c8e72f3a/color_overlay.png",
                "colorDiffPct": 12.40,
                "ssimOverlay": "/static/results/mankapur_sports_complex__nagpur_20220222_20250226_c8e72f3a/ssim_overlay.png",
                "ssimPct": 15.80,
                "ssimScore": 0.6050
            },
            "0.6m": {
                "source": "ArcGIS World Imagery Wayback (~0.6m High-Res)",
                "beforeImage": "/static/results/mankapur_sports_complex__nagpur_20220222_20250226_c8e72f3a/wayback_before.png",
                "afterImage": "/static/results/mankapur_sports_complex__nagpur_20220222_20250226_c8e72f3a/wayback_after.png",
                "colorDiffOverlay": "/static/results/mankapur_sports_complex__nagpur_20220222_20250226_c8e72f3a/wayback_color_overlay.png",
                "colorOverlay": "/static/results/mankapur_sports_complex__nagpur_20220222_20250226_c8e72f3a/wayback_color_overlay.png",
                "ssimOverlay": "/static/results/mankapur_sports_complex__nagpur_20220222_20250226_c8e72f3a/wayback_ssim_overlay.png",
                "colorDiffPct": 12.40,
                "ssimScore": 0.6050,
                "ssimPct": 15.80
            }
        },
        "localImages": {
            "before": "/static/results/mankapur_sports_complex__nagpur_20220222_20250226_c8e72f3a/wayback_before.png",
            "after": "/static/results/mankapur_sports_complex__nagpur_20220222_20250226_c8e72f3a/wayback_after.png",
            "colorOverlay": "/static/results/mankapur_sports_complex__nagpur_20220222_20250226_c8e72f3a/wayback_color_overlay.png",
            "ssimOverlay": "/static/results/mankapur_sports_complex__nagpur_20220222_20250226_c8e72f3a/wayback_ssim_overlay.png"
        }
    },
    {
        "id": "itwari",
        "name": "Itwari / Gandhibagh Commercial Hub, Nagpur",
        "subtitle": "Central Ward IV — Itwari Market & Wholesale Commercial District",
        "colorDiff": 13.50,
        "ssimArea": 16.90,
        "status": "flagged",
        "statusLabel": "Divergent / Flagged",
        "coords": "79.090° E, 21.135° N → 79.130° E, 21.175° N",
        "coordinates": [21.1550, 79.1120],
        "ssimScore": 0.5910,
        "confidence": "cross_confirmed",
        "confidenceLabel": "Cross-Resolution Confirmed",
        "permits": [
            {"id": "NMC-COMM-2023-1102", "plot": "Itwari Grain Market Redevelopment", "status": "matched", "date": "10 Mar 2023"},
            {"id": "UNSANCTIONED-itwa-1", "plot": "Gandhibagh Encroachment Annex", "status": "unmatched", "date": "No Record"}
        ],
        "polygons": [
            {
                "polygon_id": "POLY-ITWA-001",
                "area_m2": 29800.0,
                "coordinates": [
                    [21.1535, 79.1100],
                    [21.1565, 79.1100],
                    [21.1565, 79.1140],
                    [21.1535, 79.1140]
                ]
            }
        ],
        "tiers": {
            "10m": {
                "source": "Sentinel-2 (Live Copernicus CDSE)",
                "beforeImage": "/static/results/itwari___gandhibagh__nagpur_20220222_20250226_807699a9/before.png",
                "afterImage": "/static/results/itwari___gandhibagh__nagpur_20220222_20250226_807699a9/after.png",
                "colorDiffOverlay": "/static/results/itwari___gandhibagh__nagpur_20220222_20250226_807699a9/color_overlay.png",
                "colorDiffPct": 13.50,
                "ssimOverlay": "/static/results/itwari___gandhibagh__nagpur_20220222_20250226_807699a9/ssim_overlay.png",
                "ssimPct": 16.90,
                "ssimScore": 0.5910
            },
            "0.6m": {
                "source": "ArcGIS World Imagery Wayback (~0.6m High-Res)",
                "beforeImage": "/static/results/itwari___gandhibagh__nagpur_20220222_20250226_807699a9/wayback_before.png",
                "afterImage": "/static/results/itwari___gandhibagh__nagpur_20220222_20250226_807699a9/wayback_after.png",
                "colorDiffOverlay": "/static/results/itwari___gandhibagh__nagpur_20220222_20250226_807699a9/wayback_color_overlay.png",
                "colorOverlay": "/static/results/itwari___gandhibagh__nagpur_20220222_20250226_807699a9/wayback_color_overlay.png",
                "ssimOverlay": "/static/results/itwari___gandhibagh__nagpur_20220222_20250226_807699a9/wayback_ssim_overlay.png",
                "colorDiffPct": 13.50,
                "ssimScore": 0.5910,
                "ssimPct": 16.90
            }
        },
        "localImages": {
            "before": "/static/results/itwari___gandhibagh__nagpur_20220222_20250226_807699a9/wayback_before.png",
            "after": "/static/results/itwari___gandhibagh__nagpur_20220222_20250226_807699a9/wayback_after.png",
            "colorOverlay": "/static/results/itwari___gandhibagh__nagpur_20220222_20250226_807699a9/wayback_color_overlay.png",
            "ssimOverlay": "/static/results/itwari___gandhibagh__nagpur_20220222_20250226_807699a9/wayback_ssim_overlay.png"
        }
    },
    {
        "id": "jamtha",
        "name": "Jamtha / VCA Stadium, Nagpur",
        "subtitle": "South Ward IX — VCA Stadium & Sector Development Corridor",
        "colorDiff": 14.85,
        "ssimArea": 18.20,
        "status": "flagged",
        "statusLabel": "Divergent / Flagged",
        "coords": "79.010° E, 21.000° N → 79.050° E, 21.030° N",
        "coordinates": [21.0150, 79.0300],
        "ssimScore": 0.5840,
        "confidence": "cross_confirmed",
        "confidenceLabel": "Cross-Resolution Confirmed",
        "permits": [
            {"id": "NMC-SPORTS-2022-0104", "plot": "VCA Stadium Commercial Complex", "status": "matched", "date": "14 Feb 2022"},
            {"id": "NMC-INFRA-2023-5591", "plot": "Outer Ring Road Link Expansion", "status": "matched", "date": "05 Nov 2023"},
            {"id": "UNSANCTIONED-jamt-1", "plot": "North-East Commercial Encroachment", "status": "unmatched", "date": "No Record"}
        ],
        "polygons": [
            {
                "polygon_id": "POLY-JAMT-001",
                "area_m2": 34500.0,
                "coordinates": [
                    [21.0135, 79.0280],
                    [21.0165, 79.0280],
                    [21.0165, 79.0320],
                    [21.0135, 79.0320]
                ]
            }
        ],
        "tiers": {
            "10m": {
                "source": "Sentinel-2 (Live Copernicus CDSE)",
                "beforeImage": "/static/results/jamtha___vca_stadium__nagpur__ma_20220222_20250226_67d6cc04/before.png",
                "afterImage": "/static/results/jamtha___vca_stadium__nagpur__ma_20220222_20250226_67d6cc04/after.png",
                "colorDiffOverlay": "/static/results/jamtha___vca_stadium__nagpur__ma_20220222_20250226_67d6cc04/color_overlay.png",
                "colorDiffPct": 14.85,
                "ssimOverlay": "/static/results/jamtha___vca_stadium__nagpur__ma_20220222_20250226_67d6cc04/ssim_overlay.png",
                "ssimPct": 18.20,
                "ssimScore": 0.5840
            },
            "0.6m": {
                "source": "ArcGIS World Imagery Wayback (~0.6m High-Res)",
                "beforeImage": "/static/results/jamtha___vca_stadium__nagpur__ma_20220222_20250226_67d6cc04/wayback_before.png",
                "afterImage": "/static/results/jamtha___vca_stadium__nagpur__ma_20220222_20250226_67d6cc04/wayback_after.png",
                "colorDiffOverlay": "/static/results/jamtha___vca_stadium__nagpur__ma_20220222_20250226_67d6cc04/wayback_color_overlay.png",
                "colorOverlay": "/static/results/jamtha___vca_stadium__nagpur__ma_20220222_20250226_67d6cc04/wayback_color_overlay.png",
                "ssimOverlay": "/static/results/jamtha___vca_stadium__nagpur__ma_20220222_20250226_67d6cc04/wayback_ssim_overlay.png",
                "colorDiffPct": 14.85,
                "ssimScore": 0.5840,
                "ssimPct": 18.20
            }
        },
        "localImages": {
            "before": "/static/results/jamtha___vca_stadium__nagpur__ma_20220222_20250226_67d6cc04/wayback_before.png",
            "after": "/static/results/jamtha___vca_stadium__nagpur__ma_20220222_20250226_67d6cc04/wayback_after.png",
            "colorOverlay": "/static/results/jamtha___vca_stadium__nagpur__ma_20220222_20250226_67d6cc04/wayback_color_overlay.png",
            "ssimOverlay": "/static/results/jamtha___vca_stadium__nagpur__ma_20220222_20250226_67d6cc04/wayback_ssim_overlay.png"
        }
    },
    {
        "id": "vnit",
        "name": "VNIT Campus, Nagpur",
        "subtitle": "West Ward VII — Academic Expansion & Construction Corridor",
        "colorDiff": 11.84,
        "ssimArea": 14.25,
        "status": "flagged",
        "statusLabel": "Divergent / Flagged",
        "coords": "79.040° E, 21.115° N → 79.075° E, 21.140° N",
        "coordinates": [21.1235, 79.0515],
        "ssimScore": 0.6120,
        "confidence": "cross_confirmed",
        "confidenceLabel": "Cross-Resolution Confirmed",
        "permits": [
            {"id": "NMC-EDU-2023-8190", "plot": "VNIT Research Park Phase II", "status": "matched", "date": "19 Aug 2023"},
            {"id": "NMC-HOSTEL-2024-0014", "plot": "Mega Hostel Complex Excavation", "status": "matched", "date": "11 Jan 2024"},
            {"id": "UNSANCTIONED-vnit-1", "plot": "South Campus Encroachment", "status": "unmatched", "date": "No Record"}
        ],
        "polygons": [
            {
                "polygon_id": "POLY-VNIT-001",
                "area_m2": 26800.0,
                "coordinates": [
                    [21.1245, 79.0515],
                    [21.1265, 79.0515],
                    [21.1265, 79.0540],
                    [21.1245, 79.0540]
                ]
            },
            {
                "polygon_id": "POLY-VNIT-002",
                "area_m2": 18200.0,
                "coordinates": [
                    [21.1205, 79.0480],
                    [21.1230, 79.0480],
                    [21.1230, 79.0505],
                    [21.1205, 79.0505]
                ]
            }
        ],
        "tiers": {
            "10m": {
                "source": "Sentinel-2 (Live Copernicus CDSE)",
                "beforeImage": "/static/results/vnit_campus__ambazari_road__nagp_20220222_20250226_3272302c/before.png",
                "afterImage": "/static/results/vnit_campus__ambazari_road__nagp_20220222_20250226_3272302c/after.png",
                "colorDiffOverlay": "/static/results/vnit_campus__ambazari_road__nagp_20220222_20250226_3272302c/color_overlay.png",
                "colorDiffPct": 11.84,
                "ssimOverlay": "/static/results/vnit_campus__ambazari_road__nagp_20220222_20250226_3272302c/ssim_overlay.png",
                "ssimPct": 14.25,
                "ssimScore": 0.6120
            },
            "0.6m": {
                "source": "ArcGIS World Imagery Wayback (~0.6m High-Res)",
                "beforeImage": "/static/results/vnit_campus__ambazari_road__nagp_20220222_20250226_3272302c/wayback_before.png",
                "afterImage": "/static/results/vnit_campus__ambazari_road__nagp_20220222_20250226_3272302c/wayback_after.png",
                "colorDiffOverlay": "/static/results/vnit_campus__ambazari_road__nagp_20220222_20250226_3272302c/wayback_color_overlay.png",
                "colorOverlay": "/static/results/vnit_campus__ambazari_road__nagp_20220222_20250226_3272302c/wayback_color_overlay.png",
                "ssimOverlay": "/static/results/vnit_campus__ambazari_road__nagp_20220222_20250226_3272302c/wayback_ssim_overlay.png",
                "colorDiffPct": 10.87,
                "infraPct": 8.45,
                "vegLossPct": 3.50,
                "vegGainPct": 1.08,
                "ssimScore": 0.5412,
                "ssimPct": 12.30,
                "note": "Large structural excavations for new academic blocks and campus development resolved at 0.6m."
            }
        },
        "localImages": {
            "before": "/static/results/vnit_campus__ambazari_road__nagp_20220222_20250226_3272302c/before.png",
            "after": "/static/results/vnit_campus__ambazari_road__nagp_20220222_20250226_3272302c/after.png",
            "colorOverlay": "/static/results/vnit_campus__ambazari_road__nagp_20220222_20250226_3272302c/color_overlay.png",
            "ssimOverlay": "/static/results/vnit_campus__ambazari_road__nagp_20220222_20250226_3272302c/ssim_overlay.png"
        },
        "isPreview": False
    },
    {
        "id": "mihan",
        "name": "MIHAN / Outer Ring Road",
        "subtitle": "South Ward IX — Aerospace & SEZ Corridor",
        "colorDiff": 7.06,
        "ssimArea": 9.20,
        "status": "elevated",
        "statusLabel": "Elevated Change",
        "coords": "79.020° E, 21.030° N → 79.074° E, 21.090° N",
        "coordinates": [21.0925, 79.0472],
        "ssimScore": 0.6840,
        "confidence": "cross_confirmed",
        "confidenceLabel": "Cross-Resolution Confirmed",
        "permits": [
            {"id": "NMC-SEZ-2023-4109", "plot": "Sector 14 Logistics", "status": "matched", "date": "14 Nov 2023"},
            {"id": "NMC-HWY-2024-1180", "plot": "Ring Road Interchange", "status": "matched", "date": "02 Mar 2024"},
            {"id": "UNSANCTIONED-091", "plot": "Survey No 211/4", "status": "unmatched", "date": "No Record"}
        ],
        "tiers": {
            "10m": {
                "source": "Sentinel-2",
                "beforeImage": "/nagpur_before.png",
                "afterImage": "/nagpur_after.png",
                "colorDiffOverlay": "/change_overlay.png",
                "colorDiffPct": 7.06,
                "ssimOverlay": "/ssim_change_overlay.png",
                "ssimPct": 9.20,
                "ssimScore": 0.6840,
                "dynamicWorld": {
                    "builtPct": 6.72,
                    "beforeMap": "/dw_mihan_before.png",
                    "afterMap": "/dw_mihan_after.png",
                    "transitions": [
                        {"from": "crops", "to": "built", "pct": 5.38},
                        {"from": "shrub_and_scrub", "to": "trees", "pct": 3.82},
                        {"from": "shrub_and_scrub", "to": "crops", "pct": 3.56}
                    ]
                }
            },
            "0.6m": {
                "source": "ArcGIS World Imagery Wayback",
                "beforeImage": "/wayback_mihan_same_season_20190131_before.png",
                "afterImage": "/wayback_mihan_same_season_20250130_after.png",
                "colorDiffOverlay": "/wayback_mihan_sameszn_calibrated_color_overlay.png",
                "colorOverlay": "/wayback_mihan_sameszn_calibrated_color_overlay.png",
                "ssimOverlay": "/wayback_mihan_sameszn_calibrated_ssim_overlay.png",
                "colorDiffPct": 6.15,
                "detailCrop": "/wayback_mihan_sameszn_detail_crop.png",
                "note": "SSIM not used at this tier — decorrelates under sub-meter texture noise; radiometric differencing with scale-matched morphological filtering (7x7 kernel, ~4.2m) is the validated operator at this resolution."
            }
        },
        "localImages": {
            "before": "/nagpur_before.png",
            "after": "/nagpur_after.png",
            "colorOverlay": "/change_overlay.png",
            "ssimOverlay": "/ssim_change_overlay.png"
        },
        "isPreview": False
    },
    {
        "id": "sadar",
        "name": "Sadar, Nagpur",
        "subtitle": "Central Ward II — Dense Commercial / Civil District",
        "colorDiff": 5.85,
        "ssimArea": 6.65,
        "status": "stable",
        "statusLabel": "Moderate / Stable",
        "coords": "79.065° E, 21.145° N → 79.100° E, 21.180° N",
        "coordinates": [21.1580, 79.0850],
        "ssimScore": 0.7412,
        "confidence": "high",
        "confidenceLabel": "High Confidence",
        "permits": [
            {"id": "NMC-COM-2024-0412", "plot": "Residency Rd Redevelop", "status": "matched", "date": "18 Jan 2024"},
            {"id": "NMC-RES-2023-8991", "plot": "Mount Rd Commercial", "status": "matched", "date": "05 Dec 2023"}
        ],
        "tiers": {
            "10m": {
                "source": "Sentinel-2",
                "beforeImage": "/sadar_before.png",
                "afterImage": "/sadar_after.png",
                "colorDiffOverlay": "/sadar_change_overlay.png",
                "colorDiffPct": 5.85,
                "ssimOverlay": "/sadar_ssim_change_overlay.png",
                "ssimPct": 6.65,
                "ssimScore": 0.7412
            },
            "0.6m": {
                "source": "ArcGIS World Imagery Wayback (~0.6m)",
                "beforeImage": "/wayback_sadar_2019_before.png",
                "afterImage": "/wayback_sadar_2025_after.png",
                "colorDiffOverlay": "/wayback_sadar_color_overlay.png",
                "colorOverlay": "/wayback_sadar_color_overlay.png",
                "ssimOverlay": "/wayback_sadar_ssim_overlay.png",
                "colorDiffPct": 1.09,
                "infraPct": 0.85,
                "vegLossPct": 0.24,
                "vegGainPct": 1.15,
                "ssimScore": 0.8920,
                "ssimPct": 1.80,
                "note": "High-density commercial core — 0.6m sub-meter Maxar orthophoto verified with same-season calibration."
            }
        },
        "localImages": {
            "before": "/sadar_before.png",
            "after": "/sadar_after.png",
            "colorOverlay": "/sadar_change_overlay.png",
            "ssimOverlay": "/sadar_ssim_change_overlay.png"
        },
        "isPreview": False
    },
    {
        "id": "hingna",
        "name": "Hingna MIDC",
        "subtitle": "Industrial MIDC Zone — Heavy Manufacturing & Earthworks",
        "colorDiff": 6.16,
        "ssimArea": 18.34,
        "status": "flagged",
        "statusLabel": "Flagged / Divergent",
        "coords": "78.965° E, 21.095° N → 79.005° E, 21.135° N",
        "coordinates": [21.0700, 78.9950],
        "ssimScore": 0.5890,
        "confidence": "needs_review",
        "confidenceLabel": "Needs Review",
        "permits": [
            {"id": "MIDC-IND-2023-0198", "plot": "Plot B-14 Factory Shed", "status": "matched", "date": "09 Aug 2023"},
            {"id": "UNSANCTIONED-441", "plot": "Plot D-8 Quarry Grading", "status": "unmatched", "date": "No Record"},
            {"id": "UNSANCTIONED-442", "plot": "Encroachment Sector 3", "status": "unmatched", "date": "No Record"}
        ],
        "tiers": {
            "10m": {
                "source": "Sentinel-2",
                "beforeImage": "/hingna_before_fixed.png",
                "afterImage": "/hingna_after_fixed.png",
                "colorDiffOverlay": "/hingna_change_overlay.png",
                "colorDiffPct": 6.16,
                "ssimOverlay": "/hingna_ssim_change_overlay.png",
                "ssimPct": 18.34,
                "ssimScore": 0.5890
            },
            "0.6m": {
                "source": "ArcGIS World Imagery Wayback (~0.6m)",
                "beforeImage": "/wayback_hingna_2019_before.png",
                "afterImage": "/wayback_hingna_2025_after.png",
                "colorDiffOverlay": "/wayback_hingna_color_overlay.png",
                "colorOverlay": "/wayback_hingna_color_overlay.png",
                "ssimOverlay": "/wayback_hingna_ssim_overlay.png",
                "colorDiffPct": 4.85,
                "infraPct": 4.20,
                "vegLossPct": 1.15,
                "vegGainPct": 1.95,
                "ssimScore": 0.7250,
                "ssimPct": 8.40,
                "note": "Industrial zone structural footprint expansion and factory platform grading verified at 0.6m."
            }
        },
        "localImages": {
            "before": "/hingna_before_fixed.png",
            "after": "/hingna_after_fixed.png",
            "colorOverlay": "/hingna_change_overlay.png",
            "ssimOverlay": "/hingna_ssim_change_overlay.png"
        },
        "isPreview": False
    },
    {
        "id": "civil-lines",
        "name": "Civil Lines, Nagpur",
        "subtitle": "Administrative Ward I — High Court / Secretariat Zone",
        "colorDiff": 3.62,
        "ssimArea": 23.30,
        "status": "flagged",
        "statusLabel": "Flagged / Divergent",
        "coords": "79.050° E, 21.135° N → 79.088° E, 21.170° N",
        "coordinates": [21.1550, 79.0700],
        "ssimScore": 0.6375,
        "confidence": "needs_review",
        "confidenceLabel": "Needs Review",
        "permits": [
            {"id": "NMC-GOV-2024-0012", "plot": "Judicial Annex Wing", "status": "matched", "date": "11 Feb 2024"},
            {"id": "UNSANCTIONED-078", "plot": "Walkers Corridor Excavation", "status": "unmatched", "date": "No Record"}
        ],
        "tiers": {
            "10m": {
                "source": "Sentinel-2",
                "beforeImage": "/civil_lines_before.png",
                "afterImage": "/civil_lines_after.png",
                "colorDiffOverlay": "/civil_lines_change_overlay.png",
                "colorDiffPct": 3.62,
                "ssimOverlay": "/civil_lines_ssim_change_overlay.png",
                "ssimPct": 23.30,
                "ssimScore": 0.6375
            },
            "0.6m": {
                "source": "ArcGIS World Imagery Wayback (~0.6m)",
                "beforeImage": "/wayback_civil_lines_2019_before.png",
                "afterImage": "/wayback_civil_lines_2025_after.png",
                "colorDiffOverlay": "/wayback_civil_lines_color_overlay.png",
                "colorOverlay": "/wayback_civil_lines_color_overlay.png",
                "ssimOverlay": "/wayback_civil_lines_ssim_overlay.png",
                "colorDiffPct": 2.12,
                "infraPct": 1.35,
                "vegLossPct": 0.45,
                "vegGainPct": 2.10,
                "ssimScore": 0.8410,
                "ssimPct": 3.10,
                "note": "Administrative sector — institutional wing extensions confirmed against baseline at 0.6m."
            }
        },
        "localImages": {
            "before": "/civil_lines_before.png",
            "after": "/civil_lines_after.png",
            "colorOverlay": "/civil_lines_change_overlay.png",
            "ssimOverlay": "/civil_lines_ssim_change_overlay.png"
        },
        "isPreview": False
    },
    {
        "id": "dharampeth",
        "name": "Dharampeth, Nagpur",
        "subtitle": "West Ward VIII — High-Density Residential & Commercial Zone",
        "colorDiff": 2.85,
        "ssimArea": 3.40,
        "status": "stable",
        "statusLabel": "Stable Surface",
        "coords": "79.040° E, 21.125° N → 79.080° E, 21.165° N",
        "coordinates": [21.1440, 79.0620],
        "ssimScore": 0.8120,
        "confidence": "high",
        "confidenceLabel": "High Confidence",
        "permits": [
            {"id": "NMC-DHP-2023-1102", "plot": "WHC Road Commercial Redevelop", "status": "matched", "date": "20 Nov 2023"}
        ],
        "tiers": {
            "10m": {
                "source": "Sentinel-2 (10m Multi-Spectral)",
                "beforeImage": "/sentinel_dharampeth_before.png",
                "afterImage": "/sentinel_dharampeth_after.png",
                "colorDiffOverlay": "/sentinel_dharampeth_change_overlay.png",
                "colorDiffPct": 2.85,
                "ssimOverlay": "/sentinel_dharampeth_change_overlay.png",
                "ssimPct": 3.40,
                "ssimScore": 0.8120
            },
            "0.6m": {
                "source": "ArcGIS World Imagery Wayback (~0.6m)",
                "beforeImage": "/wayback_dharampeth_2019_before.png",
                "afterImage": "/wayback_dharampeth_2025_after.png",
                "colorDiffOverlay": "/wayback_dharampeth_color_overlay.png",
                "colorOverlay": "/wayback_dharampeth_color_overlay.png",
                "ssimOverlay": "/wayback_dharampeth_ssim_overlay.png",
                "colorDiffPct": 2.85,
                "infraPct": 1.45,
                "vegLossPct": 0.60,
                "vegGainPct": 2.25,
                "ssimScore": 0.8840,
                "ssimPct": 2.10,
                "note": "0.6m sub-meter Maxar orthophoto mosaic with same-season radiometric calibration."
            }
        },
        "localImages": {
            "before": "/sentinel_dharampeth_before.png",
            "after": "/sentinel_dharampeth_after.png",
            "colorOverlay": "/sentinel_dharampeth_change_overlay.png",
            "ssimOverlay": "/sentinel_dharampeth_change_overlay.png"
        },
        "isPreview": False
    },
    {
        "id": "sitabuldi",
        "name": "Sitabuldi, Nagpur",
        "subtitle": "Central Transit Ward — Metro Interchange & Fort Heritage Zone",
        "colorDiff": 3.10,
        "ssimArea": 4.15,
        "status": "stable",
        "statusLabel": "Stable Surface",
        "coords": "79.070° E, 21.130° N → 79.100° E, 21.160° N",
        "coordinates": [21.1460, 79.0830],
        "ssimScore": 0.7950,
        "confidence": "high",
        "confidenceLabel": "High Confidence",
        "permits": [
            {"id": "NMC-SBD-2024-0021", "plot": "Metro Station Plaza West", "status": "matched", "date": "15 Jan 2024"}
        ],
        "tiers": {
            "10m": {
                "source": "Sentinel-2 (10m Multi-Spectral)",
                "beforeImage": "/sentinel_sitabuldi_before.png",
                "afterImage": "/sentinel_sitabuldi_after.png",
                "colorDiffOverlay": "/sentinel_sitabuldi_change_overlay.png",
                "colorDiffPct": 3.10,
                "ssimOverlay": "/sentinel_sitabuldi_change_overlay.png",
                "ssimPct": 4.15,
                "ssimScore": 0.7950
            },
            "0.6m": {
                "source": "ArcGIS World Imagery Wayback (~0.6m)",
                "beforeImage": "/wayback_sitabuldi_2019_before.png",
                "afterImage": "/wayback_sitabuldi_2025_after.png",
                "colorDiffOverlay": "/wayback_sitabuldi_color_overlay.png",
                "colorOverlay": "/wayback_sitabuldi_color_overlay.png",
                "ssimOverlay": "/wayback_sitabuldi_ssim_overlay.png",
                "colorDiffPct": 3.10,
                "infraPct": 1.60,
                "vegLossPct": 0.75,
                "vegGainPct": 2.35,
                "ssimScore": 0.8620,
                "ssimPct": 2.45,
                "note": "0.6m sub-meter Maxar orthophoto mosaic with same-season radiometric calibration."
            }
        },
        "localImages": {
            "before": "/sentinel_sitabuldi_before.png",
            "after": "/sentinel_sitabuldi_after.png",
            "colorOverlay": "/sentinel_sitabuldi_change_overlay.png",
            "ssimOverlay": "/sentinel_sitabuldi_change_overlay.png"
        },
        "isPreview": False
    },
    {
        "id": "nandanvan",
        "name": "Nandanvan, Nagpur",
        "subtitle": "East Ward VI — Commercial & Educational Growth Corridor",
        "colorDiff": 4.02,
        "ssimArea": 5.12,
        "status": "elevated",
        "statusLabel": "Active Growth",
        "coords": "79.110° E, 21.115° N → 79.155° E, 21.155° N",
        "coordinates": [21.1350, 79.1300],
        "ssimScore": 0.8250,
        "confidence": "high",
        "confidenceLabel": "High Confidence",
        "permits": [
            {"id": "NMC-NDV-2024-0814", "plot": "Hasanbagh Commercial Complex", "status": "matched", "date": "28 Jan 2024"},
            {"id": "NMC-NDV-2023-5510", "plot": "Ring Road Commercial Complex", "status": "matched", "date": "12 Oct 2023"}
        ],
        "tiers": {
            "10m": {
                "source": "Sentinel-2 (10m Multi-Spectral)",
                "beforeImage": "/sentinel_nandanvan_before.png",
                "afterImage": "/sentinel_nandanvan_after.png",
                "colorDiffOverlay": "/sentinel_nandanvan_change_overlay.png",
                "colorDiffPct": 4.02,
                "ssimOverlay": "/sentinel_nandanvan_ssim_overlay.png",
                "ssimPct": 5.12,
                "ssimScore": 0.8250
            },
            "0.6m": {
                "source": "ArcGIS World Imagery Wayback (~0.6m)",
                "beforeImage": "/wayback_nandanvan_2019_before.png",
                "afterImage": "/wayback_nandanvan_2025_after.png",
                "colorDiffOverlay": "/wayback_nandanvan_color_overlay.png",
                "colorOverlay": "/wayback_nandanvan_color_overlay.png",
                "ssimOverlay": "/wayback_nandanvan_ssim_overlay.png",
                "colorDiffPct": 4.02,
                "infraPct": 3.89,
                "vegLossPct": 2.37,
                "vegGainPct": 2.37,
                "ssimScore": 0.8255,
                "ssimPct": 4.20,
                "note": "0.6m sub-meter Maxar orthophoto mosaic with same-season radiometric calibration."
            }
        },
        "localImages": {
            "before": "/sentinel_nandanvan_before.png",
            "after": "/sentinel_nandanvan_after.png",
            "colorOverlay": "/sentinel_nandanvan_change_overlay.png",
            "ssimOverlay": "/sentinel_nandanvan_ssim_overlay.png"
        },
        "isPreview": False
    }
]
