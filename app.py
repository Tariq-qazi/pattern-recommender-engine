if submitted:
    latest_q = area_data["quarter"].max()
    latest_data = area_data[area_data["quarter"] == latest_q]

    matched = latest_data[
        (latest_data["type"] == unit_type) &
        (latest_data["rooms"] == room_count)
    ]

    if matched.empty:
        st.warning("❌ No matching zones found for the latest quarter.")
    else:
        st.success(f"✅ {len(matched)} zones matched for {latest_q}.")

        # Add pattern bucket
        enriched = pd.merge(matched, pattern_matrix[["PatternID", "Bucket"]], left_on="pattern_id", right_on="PatternID", how="left")

        # Define display order for buckets
        bucket_order = [
            "🟢 Strong Buy",
            "🟡 Cautious Buy / Watch",
            "🟠 Hold / Neutral",
            "🔁 Rotation Candidate",
            "🧭 Strategic Waitlist",
            "🔴 Caution / Avoid",
            "❓ Unclassified"
        ]
        enriched["bucket_rank"] = enriched["Bucket"].apply(lambda b: bucket_order.index(b) if b in bucket_order else len(bucket_order))

        enriched = enriched.sort_values("bucket_rank")

        for bucket in bucket_order:
            bucket_df = enriched[enriched["Bucket"] == bucket]
            if not bucket_df.empty:
                st.subheader(f"{bucket} ({len(bucket_df)} areas)")

                area_list = bucket_df["area"].drop_duplicates().tolist()
                for area in area_list:
                    st.markdown(f"- {area}")

                # Show one representative insight
                sample_pid = bucket_df.iloc[0]["pattern_id"]
                pattern_row = pattern_matrix[pattern_matrix["PatternID"] == sample_pid].iloc[0]
                st.markdown(f"**🧠 Insight ({view_mode}):**\n\n{pattern_row[f'Insight_{view_mode}']}")
                st.markdown(f"**✅ Recommendation ({view_mode}):**\n\n{pattern_row[f'Recommendation_{view_mode}']}")
