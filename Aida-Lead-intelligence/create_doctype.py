#!/usr/bin/env python3
"""
Script to manually create the Aida Lead Generation DocType in Frappe
Run this from the bench root directory
"""

import os
import sys
import json

# Add bench to path
bench_path = os.path.abspath('.')
sys.path.insert(0, bench_path)

# Import frappe
import frappe

def create_doctype():
    """Create the Aida Lead Generation DocType"""
    
    # Check if DocType already exists
    if frappe.db.exists("DocType", "Aida Lead Generation"):
        print("DocType 'Aida Lead Generation' already exists!")
        return
    
    print("Creating DocType 'Aida Lead Generation'...")
    
    # Create the DocType
    doc = frappe.new_doc("DocType")
    doc.doctype = "DocType"
    doc.name = "Aida Lead Generation"
    doc.module = "Aida Lead Intelligence"
    doc.istable = 0
    doc.issingle = 0
    doc.istree = 0
    doc.allow_import = 1
    doc.allow_rename = 1
    doc.autoname = "format:AIDA-LEAD-{####}"
    doc.engine = "InnoDB"
    doc.track_changes = 1
    doc.track_views = 1
    doc.index_web_pages_for_search = 1
    
    # Define fields
    fields = [
        {
            "fieldname": "source_section",
            "fieldtype": "Section Break",
            "label": "Lead Source Configuration",
            "collapsible": 0
        },
        {
            "fieldname": "source",
            "fieldtype": "Select",
            "label": "Lead Source",
            "options": "gmaps\napollo",
            "reqd": 1,
            "default": "gmaps",
            "in_standard_filter": 1
        },
        {
            "fieldname": "search_terms",
            "fieldtype": "Data",
            "label": "Search Terms (comma-separated)",
            "reqd": 1,
            "default": "restaurant"
        },
        {
            "fieldname": "location",
            "fieldtype": "Data",
            "label": "Location",
            "reqd": 1,
            "default": "New York, USA"
        },
        {
            "fieldname": "max_leads",
            "fieldtype": "Int",
            "label": "Max Leads",
            "reqd": 1,
            "default": 10
        },
        {
            "fieldname": "require_email",
            "fieldtype": "Check",
            "label": "Require Email",
            "default": 0
        },
        {
            "fieldname": "require_phone",
            "fieldtype": "Check",
            "label": "Require Phone",
            "default": 0
        },
        {
            "fieldname": "min_rating",
            "fieldtype": "Data",
            "label": "Min Rating (e.g., 4)"
        },
        {
            "fieldname": "apollo_section",
            "fieldtype": "Section Break",
            "label": "Apollo Configuration",
            "collapsible": 0
        },
        {
            "fieldname": "apollo_url",
            "fieldtype": "Data",
            "label": "Apollo Saved Search URL"
        },
        {
            "fieldname": "apollo_page",
            "fieldtype": "Int",
            "label": "Apollo Page",
            "default": 1
        },
        {
            "fieldname": "results_section",
            "fieldtype": "Section Break",
            "label": "Results",
            "collapsible": 0
        },
        {
            "fieldname": "status",
            "fieldtype": "Select",
            "label": "Status",
            "options": "Draft\nIn Progress\nCompleted\nFailed",
            "default": "Draft",
            "read_only": 1,
            "in_standard_filter": 1
        },
        {
            "fieldname": "generated_count",
            "fieldtype": "Int",
            "label": "Generated Count",
            "read_only": 1
        },
        {
            "fieldname": "leads_data",
            "fieldtype": "JSON",
            "label": "Leads Data",
            "read_only": 1
        },
        {
            "fieldname": "meta_tab",
            "fieldtype": "Tab Break",
            "label": "Meta"
        }
    ]
    
    # Add fields to DocType
    for field_data in fields:
        field = doc.append("fields", {})
        for key, value in field_data.items():
            setattr(field, key, value)
    
    # Set field order
    doc.field_order = [field["fieldname"] for field in fields]
    
    # Add permissions
    permission = doc.append("permissions", {})
    permission.role = "System Manager"
    permission.create = 1
    permission.read = 1
    permission.write = 1
    permission.delete = 1
    permission.submit = 1
    permission.cancel = 1
    permission.amend = 1
    permission.print = 1
    permission.email = 1
    permission.export = 1
    permission.share = 1
    permission.report = 1
    
    # Add actions
    action = doc.append("actions", {})
    action.label = "Generate Leads"
    action.action = "aida_lead_intelligence.aida_lead_intelligence.doctype.aida_lead_generation.aida_lead_generation.generate_leads"
    action.action_type = "Server Action"
    
    try:
        doc.insert()
        print("✅ DocType 'Aida Lead Generation' created successfully!")
        
        # Verify it was created
        if frappe.db.exists("DocType", "Aida Lead Generation"):
            print("✅ Verification: DocType exists in database")
        else:
            print("❌ Verification failed: DocType not found in database")
            
    except Exception as e:
        print(f"❌ Error creating DocType: {str(e)}")
        frappe.db.rollback()

if __name__ == "__main__":
    try:
        create_doctype()
    except Exception as e:
        print(f"❌ Script error: {str(e)}")
        print("Make sure you're running this from the bench root directory")
        print("and the Frappe site is running") 