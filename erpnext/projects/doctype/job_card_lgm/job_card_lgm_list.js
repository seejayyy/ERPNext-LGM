frappe.listview_settings['Job Card LGM'] = {
	// add fields to listview
	add_fields: ["status"],

	get_indicator: function (doc) {
		return [__(doc.status), {
			"Open": "red",
			"Work In Progress": "orange",
			"Completed": "green",
		}[doc.status], "status,=," + doc.status];
	}
};