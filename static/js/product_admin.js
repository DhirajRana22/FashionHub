(function($) {
    $(document).ready(function() {
        // Function to update subcategory options based on selected category
        function updateSubcategoryOptions() {
            var categoryId = $('#id_category').val();
            var subcategorySelect = $('#id_subcategory');
            
            if (!categoryId) {
                // If no category selected, clear and disable subcategory field
                subcategorySelect.empty().prop('disabled', true);
                return;
            }
            
            // Enable subcategory field
            subcategorySelect.prop('disabled', false);
            
            // Remember the current selected subcategory
            var currentSubcategory = subcategorySelect.val();
            
            // AJAX request to get subcategories for the selected category
            $.ajax({
                url: '/admin/get-subcategories/',
                data: {
                    'category_id': categoryId
                },
                dataType: 'json',
                success: function(data) {
                    // Clear current options
                    subcategorySelect.empty();
                    
                    // Add a blank option
                    subcategorySelect.append($('<option>', {
                        value: '',
                        text: '---------'
                    }));
                    
                    // Add subcategory options
                    $.each(data, function(index, subcategory) {
                        subcategorySelect.append($('<option>', {
                            value: subcategory.id,
                            text: subcategory.name
                        }));
                    });
                    
                    // Try to restore the previous selection
                    if (currentSubcategory) {
                        subcategorySelect.val(currentSubcategory);
                    }
                },
                error: function(xhr, textStatus, errorThrown) {
                    console.error("Error loading subcategories:", errorThrown);
                }
            });
        }
        
        // Bind the update function to category select change
        $('#id_category').change(updateSubcategoryOptions);
        
        // Also run the function on page load to handle edit cases
        updateSubcategoryOptions();
    });
})(django.jQuery); 