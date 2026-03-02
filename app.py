import streamlit as st
st.error("🚨 NEW VERSION LOADED – TABS SHOULD BE VISIBLE")
import pandas as pd
import math
from datetime import date

# ================= BASIC CONFIG =================
st.set_page_config(page_title="Smart Lab Attendance System", layout="wide")
st.title("🧪 Smart Lab Attendance System")

ADMIN_PASSWORD = "admin123"

student_ids = [f"31123U480{str(i).zfill(2)}" for i in range(1, 51)]
labs = ["NLP", "DBMS"]

# ================= FUNCTIONS =================
def labs_required_for_75(total, attended):
    return max(math.ceil(3 * total - 4 * attended), 0)

def save_attendance(new_df):
    try:
        df = pd.read_csv("lab_attendance.csv")
        df = pd.concat([df, new_df], ignore_index=True)
    except FileNotFoundError:
        df = new_df
    df.to_csv("lab_attendance.csv", index=False)

# ================= ROLE =================
role = st.radio("Select Role", ["Admin (Head)", "Student"])

# =================================================
# ================= ADMIN SECTION =================
# =================================================
if role == "Admin (Head)":
    password = st.text_input("Enter Admin Password", type="password")
    if password != ADMIN_PASSWORD:
        st.warning("❌ Incorrect password")
        st.stop()

    st.success("✅ Admin Access Granted")

    tab1, tab2 = st.tabs(["📋 Bulk Session Entry", "📤 Excel / CSV Upload"])

    # ---------- TAB 1: BULK SESSION ENTRY ----------
    with tab1:
        st.subheader("📋 Bulk Lab Attendance (Session-wise)")

        lab = st.selectbox("Select Lab", labs)
        att_date = st.date_input("Lab Date", date.today())

        st.write("✔ Tick Present students (untick absentees):")

        attendance = {}
        for sid in student_ids:
            attendance[sid] = st.checkbox(sid, value=True)

        if st.button("Save Attendance for This Session"):
            rows = []
            for sid, present in attendance.items():
                rows.append([
                    sid,
                    lab,
                    att_date,
                    "Present" if present else "Absent"
                ])

            new_df = pd.DataFrame(
                rows,
                columns=["student_id", "lab", "date", "status"]
            )

            save_attendance(new_df)
            st.success("✅ Bulk attendance saved successfully")

    # ---------- TAB 2: EXCEL / CSV UPLOAD ----------
    with tab2:
        st.subheader("📤 Upload Attendance Sheet (Register → Excel)")

        selected_lab = st.selectbox("Select Lab for Upload", labs)
        uploaded_file = st.file_uploader(
            "Upload Excel / CSV file",
            type=["xlsx", "csv"]
        )

        st.info("Format: student_id | 2026-02-01 | 2026-02-03 | ...  ( / = Present, a = Absent )")

        if uploaded_file:
            if uploaded_file.name.endswith(".csv"):
                sheet_df = pd.read_csv(uploaded_file)
            else:
                sheet_df = pd.read_excel(uploaded_file)

            st.dataframe(sheet_df, use_container_width=True)

            if st.button("Convert & Save Attendance"):
                rows = []

                for date_col in sheet_df.columns[1:]:
                    for _, row in sheet_df.iterrows():
                        status = "Present" if str(row[date_col]).strip() == "/" else "Absent"
                        rows.append([
                            row["student_id"],
                            selected_lab,
                            date_col,
                            status
                        ])

                new_df = pd.DataFrame(
                    rows,
                    columns=["student_id", "lab", "date", "status"]
                )

                save_attendance(new_df)
                st.success("✅ Attendance uploaded & saved successfully")

    # ---------- VIEW ALL DATA ----------
    st.subheader("📄 Full Attendance Data")
    try:
        df = pd.read_csv("lab_attendance.csv")
        st.dataframe(df, use_container_width=True)
    except FileNotFoundError:
        st.info("No attendance data yet")

# =================================================
# ================= STUDENT SECTION ===============
# =================================================
if role == "Student":
    st.subheader("👀 View Attendance")

    student_id = st.selectbox("Select Your Student ID", student_ids)

    try:
        df = pd.read_csv("lab_attendance.csv")
        student_data = df[df["student_id"] == student_id]

        if student_data.empty:
            st.info("No attendance data found")
        else:
            summary = (
                student_data
                .groupby("lab")
                .agg(
                    total_sessions=("status", "count"),
                    attended=("status", lambda x: (x == "Present").sum())
                )
                .reset_index()
            )

            summary["attendance_%"] = (
                summary["attended"] / summary["total_sessions"] * 100
            ).round(2)

            summary["labs_required_for_75"] = summary.apply(
                lambda x: labs_required_for_75(x["total_sessions"], x["attended"]),
                axis=1
            )

            st.dataframe(summary, use_container_width=True)

            for _, row in summary.iterrows():
                if row["labs_required_for_75"] > 0:
                    st.warning(
                        f"{row['lab']} Lab: Attend next {row['labs_required_for_75']} sessions to reach 75%"
                    )
                else:
                    st.success(f"{row['lab']} Lab: Attendance Safe ✅")

    except FileNotFoundError:
        st.warning("Attendance not entered yet")
