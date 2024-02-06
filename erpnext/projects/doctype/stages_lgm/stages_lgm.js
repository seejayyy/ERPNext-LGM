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
				if (r.message != false){
					console.log(frm.doc)
					var output = r.message;
					console.log(output)

					var total_weight_list = output[0]


					var batch_weight_list = output[1]

					var mixer_selection = "mixer_internal_mixer"; 
					var total_weight_name = "total_weight_table_mixer";

					if (frm.doc[mixer_selection] != 1){
						var total_weight_name = "total_weight_table_two_roll_mill";
						var mixer_no = total_weight_list.length;
						frm.doc.total_weight_table_two_roll_mill = [];
						for (var i = 0; i < mixer_no; i++){
							let row = frm.add_child(total_weight_name, {
								'formulation':total_weight_list[i][1],
								'comp_mult_factor':total_weight_list[i][3]
							});
						}
						frm.refresh_field('total_weight_table_two_roll_mill');
					}
					else{
						var mixer_no = total_weight_list.length;
						frm.doc.total_weight_table_mixer = [];
						
						for (var i = 0; i < mixer_no; i++){
							let row = frm.add_child(total_weight_name, {
								'formulation':total_weight_list[i][1],
								'mb_mult_factor':total_weight_list[i][3],
								'density_mb':total_weight_list[i][5]
							});
						}
						frm.refresh_field('total_weight_table_mixer');
					}
					for (var j = 1; j < batch_weight_list.length + 1; j++){
						var batch_weight_table_name = "batch_weight_lgm_" + j;
						frm.doc[batch_weight_table_name]= [];
						var per_weight_table = batch_weight_list[j-1];
						for (var i = 0; i < per_weight_table.length; i++){
							var ingredient_weight = per_weight_table[i][5];
							if (ingredient_weight > 0){
								frm.add_child("batch_weight_lgm_" + j, {
									'mixer_no':per_weight_table[i][1],
									'ingredient':per_weight_table[i][3],
									'ingredient_weight':ingredient_weight
								});
							}
						}
						frm.refresh_field('batch_weight_lgm_' + j);
					}
				}
			},
		});
	},

	mixer_fill_factor: function(frm){
		frm.set_value("mixer_volume_used",frm.doc.mixer_fill_factor * frm.doc.mixer_volume);
	},

	on_submit: function(frm){
		frm.call({
			method:"remove_auto_created_item",
		})
	}
});

frappe.ui.form.on('Total Weight Table LGM', {
    // cdt is Child DocType name i.e Quotation Item
    // cdn is the row name for e.g bbfcb8da6a
    // refresh: function(frm, cdt, cdn) {

    // }
})