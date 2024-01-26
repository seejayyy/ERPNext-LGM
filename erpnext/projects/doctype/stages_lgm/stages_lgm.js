// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Stages LGM', {
	// refresh: function(frm) {

	// }

	onload: function(frm){
		if (frm.doc.is_first_stage == 1){
			frm.toggle_display("previous_stage_link", false);
		}
	},
	
	is_first_stage: function(frm){
		if (frm.doc.is_first_stage == 1){
			frm.toggle_display("previous_stage_link", false);
		}
		else {
			frm.toggle_display("previous_stage_link", true);
		}
	},

	before_save: function(frm){
		frm.call({
			method:"calculate_total_weight",
			args:{
				doc:frm.doc
			},
			callback:function(r){
					var output = r.message;

					var total_weight_list = output[0]


					var batch_weight_list = output[1]

					var mixer_selection = "mixer_internal_mixer"; 
					var total_weight_name = "total_weight_table_mixer";

					if (frm.doc[mixer_selection] != 1){
						var total_weight_name = "total_weight_table_two_roll_mill";
					}
					else{
						var mixer_no = total_weight_list.length;
						frm.doc.total_weight_table_mixer = []
						for (var i = 0; i < mixer_no; i++){
							let row = frm.add_child(total_weight_name, {
								'formulation':total_weight_list[i][1],
								'mb_mult_factor':total_weight_list[i][3],
								'density_mb':total_weight_list[i][5]
							})
						}
						frm.refresh_field('total_weight_table_mixer');

						frm.doc.batch_weight_lgm= []
						for (var i = 0; i < batch_weight_list.length; i++){
							frm.add_child("batch_weight_lgm", {
								'mixer_no':batch_weight_list[i][1],
								'ingredient':batch_weight_list[i][3],
								'ingredient_weight':batch_weight_list[i][5]
							})
						}
						frm.refresh_field('batch_weight_lgm');
					}
					
					
					// frm.doc.
					// frm.set_value("mb_waste", r.message);
				
			},
		});
	},

	mixer_fill_factor: function(frm){
		frm.set_value("mixer_volume_used",frm.doc.mixer_fill_factor * frm.doc.mixer_volume);
	},
});

frappe.ui.form.on('Total Weight Table LGM', {
    // cdt is Child DocType name i.e Quotation Item
    // cdn is the row name for e.g bbfcb8da6a
    refresh: function(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
		console.log("HI");
    }
})