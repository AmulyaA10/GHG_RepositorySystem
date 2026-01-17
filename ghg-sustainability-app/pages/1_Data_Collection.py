"""
Level 1 - Data Entry Page
"""
import streamlit as st
from core.db import get_db
from core.auth import require_role
from core.config import settings
from core.ui import load_custom_css, render_ecotrack_sidebar
from core.storage import storage
from core.validation import DataValidator, ValidationError
from core.workflow import WorkflowManager
from models import Project, Criteria, ProjectData, Evidence
from sqlalchemy.orm import Session
from datetime import datetime

st.set_page_config(
    page_title=f"{settings.APP_NAME} - Data Entry",
    page_icon="📝",
    layout="wide"
)

# Load custom CSS
load_custom_css()

# Render unified sidebar
render_ecotrack_sidebar()

def check_auth():
    """Check if user is logged in and has L1 role"""
    if not st.session_state.get("user"):
        st.error("❌ Please login first")
        st.stop()

    # require_role handles the check and stops if unauthorized
    require_role(["L1"])

def create_project_form(db: Session):
    """Form to create new project"""
    st.subheader("Create New Project")

    with st.form("new_project_form"):
        col1, col2 = st.columns(2)

        with col1:
            project_name = st.text_input("Project Name*", placeholder="e.g., Q1 2024 Carbon Footprint")
            organization_name = st.text_input("Organization Name*", placeholder="e.g., Acme Corp")

        with col2:
            reporting_year = st.number_input("Reporting Year*", min_value=1990, max_value=2100, value=datetime.now().year)
            description = st.text_area("Description", placeholder="Optional project description")

        submit = st.form_submit_button("Create Project", use_container_width=True)

        if submit:
            try:
                # Validate
                DataValidator.validate_required(project_name, "Project Name")
                DataValidator.validate_required(organization_name, "Organization Name")
                DataValidator.validate_year(reporting_year)

                # Create project
                project = Project(
                    project_name=project_name,
                    organization_name=organization_name,
                    reporting_year=reporting_year,
                    description=description,
                    status="DRAFT",
                    created_by=st.session_state.user.id,
                    created_by_email=st.session_state.user.email
                )

                db.add(project)
                db.commit()
                db.refresh(project)

                # Log creation
                WorkflowManager.log_transition(
                    db=db,
                    project=project,
                    action="CREATED",
                    from_status=None,
                    to_status="DRAFT",
                    user_id=st.session_state.user.id,
                    user_role=st.session_state.user.role
                )

                st.success(f"✅ Project created successfully! Project ID: {project.id}")
                st.rerun()

            except ValidationError as e:
                st.error(f"Validation error: {e}")
            except Exception as e:
                st.error(f"Error creating project: {e}")
                db.rollback()

def data_entry_form(db: Session, project: Project):
    """Form for entering activity data for 23 criteria"""
    st.subheader(f"📝 Data Entry - {project.project_name}")

    # Project Details Card
    with st.container():
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.markdown("**📋 Project Information**")
            st.write(f"**Project:** {project.project_name}")
            st.write(f"**Organization:** {project.organization_name}")
            if project.description:
                st.caption(f"Description: {project.description}")

        with col2:
            st.markdown("**📅 Details**")
            st.write(f"**Reporting Year:** {project.reporting_year}")
            st.write(f"**Status:** `{project.status}`")
            st.write(f"**Created:** {project.created_at.strftime('%Y-%m-%d')}")

        with col3:
            # Count data entries
            data_count = db.query(ProjectData).filter(ProjectData.project_id == project.id).count()
            st.metric("Data Entries", f"{data_count}/23")

    st.markdown("---")

    # Get all criteria
    criteria_list = db.query(Criteria).filter(Criteria.is_active == True).order_by(Criteria.criteria_number).all()

    if not criteria_list:
        st.warning("No criteria found. Please run seed scripts first.")
        return

    # Organize by scope
    scopes = {}
    for criterion in criteria_list:
        if criterion.scope not in scopes:
            scopes[criterion.scope] = []
        scopes[criterion.scope].append(criterion)

    # Display by scope
    for scope_name, scope_criteria in scopes.items():
        with st.expander(f"**{scope_name}** ({len(scope_criteria)} categories)", expanded=True):
            for criterion in scope_criteria:
                # Get existing data
                existing_data = db.query(ProjectData).filter(
                    ProjectData.project_id == project.id,
                    ProjectData.criteria_id == criterion.id
                ).first()

                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    st.markdown(f"**{criterion.criteria_number}. {criterion.category}**")
                    if criterion.subcategory:
                        st.caption(criterion.subcategory)

                with col2:
                    activity_data = st.number_input(
                        f"Activity Data ({criterion.unit or 'units'})",
                        min_value=0.0,
                        value=float(existing_data.activity_data) if existing_data else 0.0,
                        step=0.01,
                        key=f"ad_{criterion.id}",
                        help=criterion.help_text
                    )

                with col3:
                    # Evidence upload
                    evidence_count = db.query(Evidence).filter(
                        Evidence.project_id == project.id,
                        Evidence.criteria_id == criterion.id
                    ).count()

                    if st.button(f"📎 Evidence ({evidence_count})", key=f"ev_btn_{criterion.id}"):
                        # Toggle evidence section for this criterion
                        current_evidence = st.session_state.get("evidence_section")
                        if current_evidence == criterion.id:
                            st.session_state.evidence_section = None
                        else:
                            st.session_state.evidence_section = criterion.id
                        st.rerun()

                # Notes
                notes = st.text_input(
                    "Notes",
                    value=existing_data.notes if existing_data else "",
                    key=f"notes_{criterion.id}",
                    placeholder="Optional notes"
                )

                # Save button and status
                col_save1, col_save2 = st.columns([2, 3])

                with col_save1:
                    if st.button(f"💾 Save", key=f"save_{criterion.id}", use_container_width=True):
                        try:
                            # Allow 0 values, but validate if > 0
                            if activity_data > 0:
                                DataValidator.validate_positive_number(activity_data, f"Criterion {criterion.criteria_number}")

                            if existing_data:
                                existing_data.activity_data = activity_data
                                existing_data.notes = notes
                                existing_data.updated_at = datetime.utcnow()
                            else:
                                project_data = ProjectData(
                                    project_id=project.id,
                                    criteria_id=criterion.id,
                                    activity_data=activity_data,
                                    unit=criterion.unit,
                                    notes=notes,
                                    entered_by=st.session_state.user.id,
                                    has_evidence=evidence_count
                                )
                                db.add(project_data)

                            db.commit()

                            # Store save confirmation in session
                            st.session_state[f"saved_{criterion.id}"] = True
                            st.rerun()

                        except ValidationError as e:
                            st.error(f"Validation error: {e}")
                        except Exception as e:
                            st.error(f"Error saving: {e}")
                            db.rollback()

                with col_save2:
                    # Show save confirmation if this criterion was just saved
                    if st.session_state.get(f"saved_{criterion.id}"):
                        st.success("✅ **Saved successfully!**")
                        # Clear the flag so it doesn't show on next render
                        del st.session_state[f"saved_{criterion.id}"]
                    # Show last updated time if data exists
                    elif existing_data and existing_data.updated_at:
                        st.info(f"💾 Last saved: {existing_data.updated_at.strftime('%H:%M on %Y-%m-%d')}")

                # Show evidence upload section if this criterion is selected
                if st.session_state.get("evidence_section") == criterion.id:
                    st.markdown("---")
                    st.markdown(f"**📎 Evidence Upload - {criterion.category}**")

                    uploaded_file = st.file_uploader(
                        "Choose file",
                        type=["pdf", "xlsx", "xls", "csv", "jpg", "jpeg", "png", "doc", "docx"],
                        key=f"uploader_{criterion.id}"
                    )

                    if uploaded_file:
                        # Create unique identifier for this upload to prevent re-processing
                        upload_id = f"{criterion.id}_{uploaded_file.name}_{uploaded_file.size}"
                        last_upload = st.session_state.get("last_evidence_upload")

                        # Check if file with same name already exists in database
                        existing = db.query(Evidence).filter(
                            Evidence.project_id == project.id,
                            Evidence.criteria_id == criterion.id,
                            Evidence.filename == uploaded_file.name
                        ).first()

                        if existing:
                            st.warning(f"⚠️ File '{uploaded_file.name}' already exists. Please rename the file or delete the existing one first.")
                            # Mark as processed to prevent showing this warning repeatedly
                            if last_upload != upload_id:
                                st.session_state.last_evidence_upload = upload_id
                        elif last_upload == upload_id:
                            # Already processed this exact upload, skip silently
                            pass
                        else:
                            # New file, process upload
                            try:
                                DataValidator.validate_file_upload(uploaded_file)

                                # Save file
                                file_path = storage.save_evidence_file(uploaded_file, project.id, criterion.id)

                                # Record in database
                                evidence = Evidence(
                                    project_id=project.id,
                                    criteria_id=criterion.id,
                                    filename=uploaded_file.name,
                                    file_path=file_path,
                                    file_size=uploaded_file.size,
                                    file_type=uploaded_file.name.split('.')[-1],
                                    uploaded_by=st.session_state.user.id
                                )
                                db.add(evidence)
                                db.commit()

                                st.success(f"✅ Evidence uploaded: {uploaded_file.name}")

                                # Update evidence count
                                project_data = db.query(ProjectData).filter(
                                    ProjectData.project_id == project.id,
                                    ProjectData.criteria_id == criterion.id
                                ).first()

                                if project_data:
                                    project_data.has_evidence = db.query(Evidence).filter(
                                        Evidence.project_id == project.id,
                                        Evidence.criteria_id == criterion.id
                                    ).count()
                                    db.commit()

                                # Mark this upload as processed
                                st.session_state.last_evidence_upload = upload_id
                                st.rerun()

                            except ValidationError as e:
                                st.error(f"Validation error: {e}")
                                st.session_state.last_evidence_upload = upload_id
                            except Exception as e:
                                st.error(f"Error uploading: {e}")
                                st.session_state.last_evidence_upload = upload_id
                                db.rollback()

                    # List existing evidence
                    evidence_list = db.query(Evidence).filter(
                        Evidence.project_id == project.id,
                        Evidence.criteria_id == criterion.id
                    ).all()

                    if evidence_list:
                        st.markdown("**Uploaded Files:**")
                        for ev in evidence_list:
                            col_e1, col_e2 = st.columns([4, 1])
                            with col_e1:
                                st.write(f"📄 {ev.filename} ({ev.file_size / 1024:.1f} KB)")
                            with col_e2:
                                if st.button("Delete", key=f"del_{ev.id}"):
                                    storage.delete_evidence_file(ev.file_path)
                                    db.delete(ev)
                                    db.commit()
                                    st.rerun()

                    if st.button("Close Evidence Upload", key=f"close_ev_{criterion.id}"):
                        st.session_state.evidence_section = None
                        st.rerun()

                st.markdown("---")

def submit_project(db: Session, project: Project):
    """Submit project for calculation"""
    st.markdown("---")
    st.subheader("Submit Project")

    # Check if data entered
    data_count = db.query(ProjectData).filter(ProjectData.project_id == project.id).count()

    # Show submission confirmation if just submitted
    if st.session_state.get(f"project_submitted_{project.id}"):
        st.success("✅ **Project submitted successfully!** It will now move to Level 2 for calculations.")
        st.balloons()
        del st.session_state[f"project_submitted_{project.id}"]

    st.info(f"**Data Entry Progress:** {data_count} / 23 criteria completed")

    if data_count == 0:
        st.error("❌ No data entered yet. Enter activity data for at least one criterion before submitting.")
        return

    # Warn if incomplete but allow submission
    if data_count < 23:
        st.warning(f"⚠️ Only {data_count} / 23 criteria completed. You can submit now, but consider completing all criteria for comprehensive calculations.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📤 Submit for Calculation", type="primary", use_container_width=True):
            try:
                can_transition, message = WorkflowManager.can_transition(
                    project.status,
                    "SUBMITTED",
                    st.session_state.user.role
                )

                if can_transition:
                    WorkflowManager.transition(
                        db=db,
                        project=project,
                        new_status="SUBMITTED",
                        user_id=st.session_state.user.id,
                        user_role=st.session_state.user.role
                    )
                    # Store submission confirmation in session
                    st.session_state[f"project_submitted_{project.id}"] = True
                    st.rerun()
                else:
                    st.error(f"Cannot submit: {message}")

            except Exception as e:
                st.error(f"Error submitting: {e}")

    with col2:
        if st.button("💾 Save as Draft", use_container_width=True):
            st.session_state[f"draft_saved_{project.id}"] = True
            st.rerun()

    # Show draft save confirmation
    if st.session_state.get(f"draft_saved_{project.id}"):
        st.success("✅ Project saved as draft")
        del st.session_state[f"draft_saved_{project.id}"]

def main():
    """Main function"""
    check_auth()

    st.title("📝 Level 1 - Data Entry")
    st.markdown("Enter activity data for GHG emissions calculations")
    st.markdown("---")

    db = next(get_db())

    try:
        # Sidebar - Project selection
        with st.sidebar:
            st.header("My Projects")

            # Search box
            search_term = st.text_input(
                "🔍 Search projects",
                placeholder="Project or organization name...",
                key="project_search_l1"
            )

            # Pagination setup
            page_size = 20
            if 'l1_project_page' not in st.session_state:
                st.session_state.l1_project_page = 1

            # Build query
            query = db.query(Project).filter(
                Project.created_by == st.session_state.user.id
            )

            # Apply search filter
            if search_term:
                from sqlalchemy import or_
                query = query.filter(
                    or_(
                        Project.project_name.ilike(f"%{search_term}%"),
                        Project.organization_name.ilike(f"%{search_term}%")
                    )
                )

            # Get total count for pagination
            total_count = query.count()
            total_pages = max(1, (total_count + page_size - 1) // page_size)

            # Ensure current page is valid
            if st.session_state.l1_project_page > total_pages:
                st.session_state.l1_project_page = total_pages

            # Get paginated results
            projects = query.order_by(Project.created_at.desc())\
                .limit(page_size)\
                .offset((st.session_state.l1_project_page - 1) * page_size)\
                .all()

            if projects:
                # Show count
                st.caption(f"Showing {len(projects)} of {total_count} projects")

                project_options = {
                    f"[{p.status}] {p.project_name} ({p.reporting_year})": p.id
                    for p in projects
                }

                selected_project_str = st.selectbox(
                    "Select Project",
                    options=list(project_options.keys()),
                    key="project_select_l1"
                )

                selected_project_id = project_options[selected_project_str]
                selected_project = db.query(Project).filter(Project.id == selected_project_id).first()

                # Pagination controls
                if total_pages > 1:
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col1:
                        if st.session_state.l1_project_page > 1:
                            if st.button("← Prev", key="prev_l1", use_container_width=True):
                                st.session_state.l1_project_page -= 1
                                st.rerun()
                    with col2:
                        st.caption(f"Page {st.session_state.l1_project_page}/{total_pages}")
                    with col3:
                        if st.session_state.l1_project_page < total_pages:
                            if st.button("Next →", key="next_l1", use_container_width=True):
                                st.session_state.l1_project_page += 1
                                st.rerun()

                st.markdown("---")
                st.markdown(f"**Status:** `{selected_project.status}`")
                st.markdown(f"**Organization:** {selected_project.organization_name}")
                st.markdown(f"**Year:** {selected_project.reporting_year}")

            else:
                if search_term:
                    st.info(f"No projects found matching '{search_term}'")
                    if st.button("Clear search", key="clear_search_l1"):
                        st.session_state.l1_project_page = 1
                        st.rerun()
                else:
                    st.info("No projects yet. Create your first project below.")
                selected_project = None

            st.markdown("---")
            if st.button("➕ Create New Project", use_container_width=True):
                st.session_state.show_create_form = True

        # Main content
        if st.session_state.get("show_create_form") or not projects:
            create_project_form(db)
        elif selected_project:
            if selected_project.status in ["DRAFT", "REJECTED"]:
                data_entry_form(db, selected_project)
                submit_project(db, selected_project)
            else:
                # Project Details Card for locked projects
                st.subheader(f"📋 {selected_project.project_name}")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Project Information**")
                    st.write(f"**Organization:** {selected_project.organization_name}")
                    st.write(f"**Reporting Year:** {selected_project.reporting_year}")
                    st.write(f"**Status:** `{selected_project.status}`")
                    if selected_project.description:
                        st.write(f"**Description:** {selected_project.description}")

                with col2:
                    st.markdown("**Timeline**")
                    st.write(f"**Created:** {selected_project.created_at.strftime('%Y-%m-%d %H:%M')}")
                    if selected_project.submitted_at:
                        st.write(f"**Submitted:** {selected_project.submitted_at.strftime('%Y-%m-%d %H:%M')}")
                    if selected_project.approved_at:
                        st.write(f"**Approved:** {selected_project.approved_at.strftime('%Y-%m-%d %H:%M')}")

                st.info(f"ℹ️ Project is in {selected_project.status} status. Data entry is locked.")

                # Option to reopen SUBMITTED projects
                if selected_project.status == "SUBMITTED":
                    st.markdown("---")
                    st.subheader("🔓 Reopen Project for Editing")

                    # Check if reopening is allowed
                    can_reopen, reopen_message = WorkflowManager.can_transition(
                        selected_project.status,
                        "DRAFT",
                        st.session_state.user.role
                    )

                    if can_reopen:
                        with st.form(f"reopen_form_{selected_project.id}"):
                            st.warning("⚠️ This will return the project to DRAFT status, allowing you to add or edit data entries.")

                            reopen_reason = st.text_area(
                                "Reason for reopening (optional):",
                                placeholder="e.g., Need to add missing Scope 2 data",
                                help="Explain why you need to reopen this project"
                            )

                            col_a, col_b = st.columns(2)
                            with col_a:
                                submit_reopen = st.form_submit_button("✓ Reopen Project", type="primary", use_container_width=True)
                            with col_b:
                                cancel_reopen = st.form_submit_button("✗ Cancel", type="secondary", use_container_width=True)

                            if submit_reopen:
                                try:
                                    WorkflowManager.transition(
                                        db=db,
                                        project=selected_project,
                                        new_status="DRAFT",
                                        user_id=st.session_state.user.id,
                                        user_role=st.session_state.user.role,
                                        comments=reopen_reason if reopen_reason else "Reopened for additional data entry"
                                    )
                                    st.success("✅ **Project reopened!** You can now add or edit data entries.")
                                    st.balloons()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error reopening project: {e}")
                    else:
                        st.info(f"Cannot reopen: {reopen_message}")

                # Show summary
                data_items = db.query(ProjectData).filter(ProjectData.project_id == selected_project.id).all()
                if data_items:
                    st.markdown("---")
                    st.subheader("📊 Data Summary")
                    for item in data_items:
                        st.write(f"**{item.criteria.category}:** {item.activity_data} {item.unit}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
