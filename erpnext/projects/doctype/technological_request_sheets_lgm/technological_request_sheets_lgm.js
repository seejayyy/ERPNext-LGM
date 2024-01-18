// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Technological Request Sheets LGM', {
	setup: function(frm) {
		frm.custom_make_buttons = {
			'Work Order': 'Create Work Order'
		};
	},

	refresh: function(frm) {
		// console.log(frm.doc.docstatus);
		if (frm.doc.docstatus === 1) {
			// adds the button to create work order
			frm.add_custom_button(__('Create Work Order LGM'), function() {
				frm.call({
					method:"create_work_order_lgm",
					args:{
						doc:frm.doc
					},
					callback:function(r){
						frappe.msgprint({
							message: __('Work Order LGM is created'),
							indicator: 'green'
						})
						return;
					},
				});
			});
		}

		// make the dashboard
		if (frm.doc.docstatus===1) {
			frm.trigger('show_dashboard');
		}
	},

	before_save: function(frm){
		frm.call({
			method:"calculate_waste",
			args:{
				doc:frm.doc
			},
			callback:function(r){
				frm.set_value("mb_waste", r.message);
			},
		});
	},

	show_dashboard: function(frm) {
		frm.call({
			method: "query_dashboard_info",
			args: {
				doc:frm.doc
			},
			callback: function (r){
				var dashboard_info = r.message;
				var bars = [];
				var message = '';
				var no_of_job_card = frm.doc.compounding_ingredients[0].select_mixer_no;
				var total_work = 1 + parseInt(no_of_job_card) + 2;

				// work order
				var title = __('Completed: Created Technological Request Sheet.\n Pending: Create Work Order.');
				bars.push({
					'title': title,
					'width': (1 / total_work * 100 ) + '%',
					'progress_class': 'progress-bar-success'
				});
				message = title;

				if (dashboard_info[0].length > 0){
					if (dashboard_info[0][0].docstatus === 1){
						title = __("Completed: Created Work Order. Pending: Create Job Cards.");
						bars.push({
							'title': title,
							'width': (1 / total_work * 100 ) + '%',
							'progress_class': 'progress-bar-success'
						});
						message = title;
					}
	
					if (dashboard_info[1].length > 0){
	
						title = __("Completed: Created Job Cards.\n Pending: Submit Job Cards.");
						bars.push({
							'title': title,
							'width': (1 / total_work * 100 ) + '%',
							'progress_class': 'progress-bar-success'
						});
						message = title;
	
						var completed_job = 0;
						for (var i = 0; i < dashboard_info[1].length; i++){
							if (dashboard_info[1][i].docstatus === 1){
								completed_job += 1;
								// not all jobs are completed
								title = __("Completed: Submitted Job {0}. Pending: Job {1}.", [completed_job, completed_job+1]);
								bars.push({
									'title': title,
									'width': (1 / total_work * 100 ) + '%',
									'progress_class': 'progress-bar-success'
								});
								message = title;
							}
						}
						if (completed_job == dashboard_info[1].length){
							// all jobs are completed
							title = __("Completed: Submitted Job {0}. Pending: None.", [completed_job]);
							bars[bars.length - 1]. title = title;
							message = title;
						}
						
					}
				}
				
				// console.log(frm);
				return frm.dashboard.add_progress(__('Status'), bars, message);
			}
		});
	},

	mixer_fill_factor_1: function(frm){
		frm.set_value("mixer_volume_used_1",frm.doc.mixer_fill_factor_1 * frm.doc.mixer_volume_1);
	},

	mixer_fill_factor_2: function(frm){
		frm.set_value("mixer_volume_used_2",frm.doc.mixer_fill_factor_2 * frm.doc.mixer_volume_2);
	},

	mixer_fill_factor_3: function(frm){
		frm.set_value("mixer_volume_used_3",frm.doc.mixer_fill_factor_3 * frm.doc.mixer_volume_3);
	},

	mixer_fill_factor_4: function(frm){
		frm.set_value("mixer_volume_used_4",frm.doc.mixer_fill_factor_4 * frm.doc.mixer_volume_4);
	},

	mixer_fill_factor_5: function(frm){
		frm.set_value("mixer_volume_used_5",frm.doc.mixer_fill_factor_5 * frm.doc.mixer_volume_5);
	},
});