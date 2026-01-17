"""
Level 2 - Calculations Page
"""
import streamlit as st
from core.db import get_db
from core.auth import require_role
from core.config import settings
from core.ui import load_custom_css, page_header, render_ecotrack_sidebar
from core.formulas import FormulaEngine
from core.workflow import WorkflowManager
from models import Project, ProjectData, Calculation, Ecoinvent
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

st.set_page_config(
    page_title=f"{settings.APP_NAME} - Calculations",
    page_icon="🧮",
    layout="wide"
)

# Load custom CSS
load_custom_css()

# Render unified sidebar
render_ecotrack_sidebar()

def check_auth():
    """Check if user is logged in and has L2 role"""
    if not st.session_state.get("user"):
        st.error("❌ Please login first")
        st.stop()

    # require_role handles the check and stops if unauthorized
    require_role(["L2"])

def ecoinvent_search(db: Session, search_term: str, scope_filter: str = None, limit: int = 50):
    """
    Server-side search in ecoinvent database using pg_trgm
    """
    query = db.query(Ecoinvent)

    if search_term:
        # Use pg_trgm similarity search
        search_filter = or_(
            Ecoinvent.search_text.ilike(f"%{search_term}%"),
            Ecoinvent.factor_name.ilike(f"%{search_term}%"),
            Ecoinvent.category.ilike(f"%{search_term}%")
        )
        query = query.filter(search_filter)

    if scope_filter and scope_filter != "All":
        query = query.filter(Ecoinvent.scope == scope_filter)

    # Order by relevance (using similarity if available)
    results = query.limit(limit).all()

    return results

def calculation_interface(db: Session, project: Project):
    """Interface for performing calculations"""
    st.subheader(f"🧮 Calculations - {project.project_name}")

    # Get project data entries
    data_entries = db.query(ProjectData).filter(
        ProjectData.project_id == project.id
    ).order_by(ProjectData.criteria_id).all()

    if not data_entries:
        st.warning("No data entries found for this project.")
        return

    # Count calculations
    calc_count = db.query(Calculation).filter(Calculation.project_id == project.id).count()
    st.info(f"**Progress:** {calc_count} / {len(data_entries)} calculations completed")

    # Process each data entry
    for data_entry in data_entries:
        criterion = data_entry.criteria

        # Check if calculation exists
        existing_calc = db.query(Calculation).filter(
            Calculation.project_id == project.id,
            Calculation.project_data_id == data_entry.id
        ).first()

        with st.expander(
            f"**{criterion.criteria_number}. {criterion.category}** - "
            f"{data_entry.activity_data} {data_entry.unit} "
            f"{'✅ Calculated' if existing_calc else '⏳ Pending'}",
            expanded=not existing_calc
        ):
            # Show calculation confirmation if just saved
            if st.session_state.get(f"calc_saved_{data_entry.id}"):
                calc_info = st.session_state[f"calc_saved_{data_entry.id}"]
                st.success(f"✅ **Calculation saved successfully!**")
                st.metric("Emissions Result", f"{calc_info['emissions']:.4f} tCO2e")
                st.caption(calc_info['calculation'])
                st.markdown("---")
                del st.session_state[f"calc_saved_{data_entry.id}"]

            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("**Activity Data:**")
                st.info(f"{data_entry.activity_data} {data_entry.unit}")
                st.caption(f"Scope: {criterion.scope}")
                st.caption(f"Category: {criterion.category}")

                if data_entry.notes:
                    st.caption(f"Notes: {data_entry.notes}")

            with col2:
                st.markdown("**Emission Factor Selection:**")

                # Search ecoinvent
                search_term = st.text_input(
                    "Search Ecoinvent Database",
                    key=f"search_{data_entry.id}",
                    placeholder="e.g., electricity grid, diesel, natural gas"
                )

                scope_filter = st.selectbox(
                    "Filter by Scope",
                    options=["All", "Scope 1", "Scope 2", "Scope 3"],
                    key=f"scope_filter_{data_entry.id}"
                )

                if search_term:
                    results = ecoinvent_search(db, search_term, scope_filter)

                    if results:
                        st.success(f"Found {len(results)} results")

                        # Display results
                        factor_options = {
                            f"{r.factor_name} ({r.emission_factor} {r.unit}) - {r.region or 'Global'}": r
                            for r in results
                        }

                        selected_factor_str = st.selectbox(
                            "Select Emission Factor",
                            options=list(factor_options.keys()),
                            key=f"factor_{data_entry.id}"
                        )

                        selected_factor = factor_options[selected_factor_str]

                        st.markdown(f"**Selected Factor Details:**")
                        st.write(f"- **Value:** {selected_factor.emission_factor} {selected_factor.unit}")
                        st.write(f"- **Scope:** {selected_factor.scope}")
                        st.write(f"- **Region:** {selected_factor.region or 'Global'}")
                        st.write(f"- **Source:** {selected_factor.source or 'N/A'}")

                        # Manual overrides
                        st.markdown("**Optional Adjustments:**")
                        col_a, col_b = st.columns(2)

                        with col_a:
                            gwp = st.number_input(
                                "GWP",
                                value=float(selected_factor.gwp),
                                min_value=0.0,
                                step=0.1,
                                key=f"gwp_{data_entry.id}",
                                help="Global Warming Potential"
                            )

                        with col_b:
                            unit_conversion = st.number_input(
                                "Unit Conversion",
                                value=1.0,
                                min_value=0.0,
                                step=0.1,
                                key=f"uc_{data_entry.id}",
                                help="Unit conversion factor"
                            )

                        # Calculate button
                        if st.button(f"Calculate Emissions", key=f"calc_{data_entry.id}", type="primary"):
                            try:
                                # Perform calculation
                                result = FormulaEngine.calculate_emissions(
                                    activity_data=data_entry.activity_data,
                                    emission_factor=selected_factor.emission_factor,
                                    gwp=gwp,
                                    unit_conversion=unit_conversion
                                )

                                # Save calculation
                                if existing_calc:
                                    # Update
                                    existing_calc.activity_data = data_entry.activity_data
                                    existing_calc.emission_factor = selected_factor.emission_factor
                                    existing_calc.emission_factor_source = f"Ecoinvent ID: {selected_factor.id}"
                                    existing_calc.gwp = gwp
                                    existing_calc.unit_conversion = unit_conversion
                                    existing_calc.emissions_kg = result['emissions_kg']
                                    existing_calc.emissions_tco2e = result['emissions_tco2e']
                                    existing_calc.scope = criterion.scope
                                    existing_calc.category = criterion.category
                                    existing_calc.formula_used = result['formula']
                                    existing_calc.calculation_breakdown = result
                                    existing_calc.calculated_by = st.session_state.user.id
                                else:
                                    # Create new
                                    calculation = Calculation(
                                        project_id=project.id,
                                        criteria_id=criterion.id,
                                        project_data_id=data_entry.id,
                                        activity_data=data_entry.activity_data,
                                        emission_factor=selected_factor.emission_factor,
                                        emission_factor_source=f"Ecoinvent ID: {selected_factor.id}",
                                        gwp=gwp,
                                        unit_conversion=unit_conversion,
                                        emissions_kg=result['emissions_kg'],
                                        emissions_tco2e=result['emissions_tco2e'],
                                        scope=criterion.scope,
                                        category=criterion.category,
                                        formula_used=result['formula'],
                                        calculation_breakdown=result,
                                        calculated_by=st.session_state.user.id
                                    )
                                    db.add(calculation)

                                db.commit()

                                # Update project totals
                                update_project_totals(db, project)

                                # Store calculation confirmation in session
                                st.session_state[f"calc_saved_{data_entry.id}"] = {
                                    'emissions': result['emissions_tco2e'],
                                    'calculation': result['calculation']
                                }
                                st.rerun()

                            except Exception as e:
                                st.error(f"Calculation error: {e}")
                                db.rollback()

                    else:
                        st.warning("No results found. Try different search terms.")

                else:
                    st.info("Enter search terms to find emission factors")

            # Show existing calculation
            if existing_calc:
                st.markdown("---")
                st.markdown("**Calculation Result:**")
                col_r1, col_r2, col_r3 = st.columns(3)

                with col_r1:
                    st.metric("Emissions (kg)", f"{existing_calc.emissions_kg:.4f}")

                with col_r2:
                    st.metric("Emissions (tCO2e)", f"{existing_calc.emissions_tco2e:.4f}")

                with col_r3:
                    st.metric("Emission Factor", f"{existing_calc.emission_factor:.4f}")

                st.caption(f"Formula: {existing_calc.formula_used}")
                st.caption(f"Source: {existing_calc.emission_factor_source}")

def update_project_totals(db: Session, project: Project):
    """Update project total emissions by scope"""
    # Aggregate by scope
    scope1_total = db.query(func.sum(Calculation.emissions_tco2e)).filter(
        Calculation.project_id == project.id,
        Calculation.scope == "Scope 1"
    ).scalar() or 0.0

    scope2_total = db.query(func.sum(Calculation.emissions_tco2e)).filter(
        Calculation.project_id == project.id,
        Calculation.scope == "Scope 2"
    ).scalar() or 0.0

    scope3_total = db.query(func.sum(Calculation.emissions_tco2e)).filter(
        Calculation.project_id == project.id,
        Calculation.scope == "Scope 3"
    ).scalar() or 0.0

    project.total_scope1 = scope1_total
    project.total_scope2 = scope2_total
    project.total_scope3 = scope3_total
    project.total_emissions = scope1_total + scope2_total + scope3_total

    db.commit()

def complete_calculations(db: Session, project: Project):
    """Submit calculations for review or send back for more data"""
    st.markdown("---")
    st.subheader("Complete Calculations")

    # Show submission confirmation if just submitted
    if st.session_state.get(f"l2_submitted_{project.id}"):
        st.success("✅ **Calculations submitted successfully!** Project is now ready for Level 3 quality review.")
        st.balloons()
        del st.session_state[f"l2_submitted_{project.id}"]

    # Show send back confirmation if just sent back
    if st.session_state.get(f"l2_sentback_{project.id}"):
        st.success("✅ **Project sent back to Data Entry!** L1 users can now add more data entries.")
        del st.session_state[f"l2_sentback_{project.id}"]

    # Check if all calculations done
    data_count = db.query(ProjectData).filter(ProjectData.project_id == project.id).count()
    calc_count = db.query(Calculation).filter(Calculation.project_id == project.id).count()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Scope 1", f"{project.total_scope1:.2f} tCO2e")

    with col2:
        st.metric("Total Scope 2", f"{project.total_scope2:.2f} tCO2e")

    with col3:
        st.metric("Total Scope 3", f"{project.total_scope3:.2f} tCO2e")

    st.metric("**Total Emissions**", f"{project.total_emissions:.2f} tCO2e")

    # Check if at least one calculation is done
    if calc_count == 0:
        st.error(f"❌ No calculations completed yet. Calculate at least one emission before submitting.")
        return

    # Warn if incomplete, but allow submission
    if calc_count < data_count:
        st.warning(f"⚠️ Only {calc_count} / {data_count} calculations completed. You can submit now, but consider completing all calculations for a complete review.")

    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button("📤 Submit for Review", type="primary", use_container_width=True):
            try:
                can_transition, message = WorkflowManager.can_transition(
                    project.status,
                    "PENDING_REVIEW",
                    st.session_state.user.role
                )

                if can_transition:
                    WorkflowManager.transition(
                        db=db,
                        project=project,
                        new_status="PENDING_REVIEW",
                        user_id=st.session_state.user.id,
                        user_role=st.session_state.user.role
                    )
                    # Store submission confirmation in session
                    st.session_state[f"l2_submitted_{project.id}"] = True
                    st.rerun()
                else:
                    st.error(f"Cannot submit: {message}")

            except Exception as e:
                st.error(f"Error submitting: {e}")

    with col2:
        # Toggle send back form
        if 'show_sendback_form' not in st.session_state:
            st.session_state.show_sendback_form = False

        if st.button("↩️ Send Back to L1", type="secondary", use_container_width=True,
                     help="Send project back to Data Entry for more entries"):
            st.session_state.show_sendback_form = True
            st.rerun()

    # Send back form (shown below the buttons)
    if st.session_state.get('show_sendback_form'):
        st.markdown("---")
        st.subheader("↩️ Send Project Back for More Data Entry")

        with st.form(f"sendback_form_{project.id}"):
            st.warning("⚠️ This will return the project to SUBMITTED status, allowing L1 users to add more data entries.")

            comments = st.text_area(
                "Reason for sending back (optional):",
                placeholder="e.g., Need more data entries for Scope 3 transportation",
                help="Explain why more data is needed"
            )

            col_a, col_b = st.columns(2)
            with col_a:
                submit_sendback = st.form_submit_button("✓ Confirm Send Back", type="primary", use_container_width=True)
            with col_b:
                cancel_sendback = st.form_submit_button("✗ Cancel", type="secondary", use_container_width=True)

            if cancel_sendback:
                st.session_state.show_sendback_form = False
                st.rerun()

            if submit_sendback:
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
                            user_role=st.session_state.user.role,
                            comments=comments if comments else "Sent back for additional data entry"
                        )
                        # Store send back confirmation in session
                        st.session_state[f"l2_sentback_{project.id}"] = True
                        st.session_state.show_sendback_form = False
                        st.rerun()
                    else:
                        st.error(f"Cannot send back: {message}")

                except Exception as e:
                    st.error(f"Error sending back: {e}")

def main():
    """Main function"""
    check_auth()

    st.title("🧮 Level 2 - Calculations")
    st.markdown("Calculate GHG emissions using emission factors from Ecoinvent database")
    st.markdown("---")

    db = next(get_db())

    try:
        # Sidebar - Project selection
        with st.sidebar:
            st.header("Projects for Calculation")

            # Search box
            search_term = st.text_input(
                "🔍 Search projects",
                placeholder="Project or organization name...",
                key="project_search_l2"
            )

            # Pagination setup
            page_size = 20
            if 'l2_project_page' not in st.session_state:
                st.session_state.l2_project_page = 1

            # Build query
            query = db.query(Project).filter(
                or_(
                    Project.status == "SUBMITTED",
                    Project.status == "UNDER_CALCULATION"
                )
            )

            # Apply search filter
            if search_term:
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
            if st.session_state.l2_project_page > total_pages:
                st.session_state.l2_project_page = total_pages

            # Get paginated results
            projects = query.order_by(Project.submitted_at.desc())\
                .limit(page_size)\
                .offset((st.session_state.l2_project_page - 1) * page_size)\
                .all()

            if projects:
                # Show count
                st.caption(f"Showing {len(projects)} of {total_count} projects")

                project_options = {
                    f"[{p.status}] {p.project_name} - {p.organization_name} ({p.reporting_year})": p.id
                    for p in projects
                }

                selected_project_str = st.selectbox(
                    "Select Project",
                    options=list(project_options.keys()),
                    key="project_select_l2"
                )

                selected_project_id = project_options[selected_project_str]
                selected_project = db.query(Project).filter(Project.id == selected_project_id).first()

                # Auto-transition to UNDER_CALCULATION if SUBMITTED
                if selected_project.status == "SUBMITTED":
                    try:
                        WorkflowManager.transition(
                            db=db,
                            project=selected_project,
                            new_status="UNDER_CALCULATION",
                            user_id=st.session_state.user.id,
                            user_role=st.session_state.user.role
                        )
                        db.refresh(selected_project)
                    except Exception as e:
                        st.error(f"Error transitioning: {e}")

                # Pagination controls
                if total_pages > 1:
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col1:
                        if st.session_state.l2_project_page > 1:
                            if st.button("← Prev", key="prev_l2", use_container_width=True):
                                st.session_state.l2_project_page -= 1
                                st.rerun()
                    with col2:
                        st.caption(f"Page {st.session_state.l2_project_page}/{total_pages}")
                    with col3:
                        if st.session_state.l2_project_page < total_pages:
                            if st.button("Next →", key="next_l2", use_container_width=True):
                                st.session_state.l2_project_page += 1
                                st.rerun()

                st.markdown("---")
                st.markdown(f"**Status:** `{selected_project.status}`")
                st.markdown(f"**Organization:** {selected_project.organization_name}")
                st.markdown(f"**Year:** {selected_project.reporting_year}")

            else:
                if search_term:
                    st.info(f"No projects found matching '{search_term}'")
                    if st.button("Clear search", key="clear_search_l2"):
                        st.session_state.l2_project_page = 1
                        st.rerun()
                else:
                    st.info("No projects pending calculation.")
                selected_project = None

        # Main content
        if selected_project:
            calculation_interface(db, selected_project)
            complete_calculations(db, selected_project)
        else:
            st.info("Select a project from the sidebar to start calculations.")

    finally:
        db.close()

if __name__ == "__main__":
    main()
