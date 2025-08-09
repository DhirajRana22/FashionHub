"""Quick Sort implementation for product sorting"""

def quick_sort_products(products, sort_by='price', order='asc'):
    """
    Quick Sort implementation for sorting products by price or rating
    
    Args:
        products: List of Product objects to sort
        sort_by: 'price' or 'rating' - field to sort by
        order: 'asc' for ascending, 'desc' for descending
    
    Returns:
        Sorted list of products
    """
    if len(products) <= 1:
        return products
    
    # Convert QuerySet to list if needed
    if hasattr(products, 'all'):
        products = list(products)
    
    return _quick_sort_recursive(products, sort_by, order)

def _quick_sort_recursive(products, sort_by, order):
    """
    Recursive Quick Sort implementation
    """
    if len(products) <= 1:
        return products
    
    # Choose pivot (middle element)
    pivot_index = len(products) // 2
    pivot = products[pivot_index]
    pivot_value = _get_sort_value(pivot, sort_by)
    
    # Partition the array
    left = []
    right = []
    equal = []
    
    for product in products:
        product_value = _get_sort_value(product, sort_by)
        
        if order == 'asc':
            if product_value < pivot_value:
                left.append(product)
            elif product_value > pivot_value:
                right.append(product)
            else:
                equal.append(product)
        else:  # desc
            if product_value > pivot_value:
                left.append(product)
            elif product_value < pivot_value:
                right.append(product)
            else:
                equal.append(product)
    
    # Recursively sort left and right partitions
    sorted_left = _quick_sort_recursive(left, sort_by, order)
    sorted_right = _quick_sort_recursive(right, sort_by, order)
    
    # Combine results
    return sorted_left + equal + sorted_right

def _get_sort_value(product, sort_by):
    """
    Get the value to sort by from a product object
    
    Args:
        product: Product object
        sort_by: 'price' or 'rating'
    
    Returns:
        Numeric value for sorting
    """
    if sort_by == 'price':
        return float(product.price)
    elif sort_by == 'rating':
        return product.average_rating
    else:
        raise ValueError(f"Invalid sort_by value: {sort_by}. Must be 'price' or 'rating'")

def hybrid_sort_products(products, primary_sort='price', secondary_sort='rating', order='asc'):
    """
    Hybrid sorting: First sort by primary field, then by secondary field for ties
    
    Args:
        products: List of Product objects to sort
        primary_sort: Primary field to sort by ('price' or 'rating')
        secondary_sort: Secondary field for tie-breaking ('price' or 'rating')
        order: 'asc' for ascending, 'desc' for descending
    
    Returns:
        Sorted list of products
    """
    if len(products) <= 1:
        return products
    
    # Convert QuerySet to list if needed
    if hasattr(products, 'all'):
        products = list(products)
    
    return _hybrid_sort_recursive(products, primary_sort, secondary_sort, order)

def _hybrid_sort_recursive(products, primary_sort, secondary_sort, order):
    """
    Recursive hybrid sort implementation
    """
    if len(products) <= 1:
        return products
    
    # Choose pivot
    pivot_index = len(products) // 2
    pivot = products[pivot_index]
    pivot_primary = _get_sort_value(pivot, primary_sort)
    pivot_secondary = _get_sort_value(pivot, secondary_sort)
    
    # Partition the array
    left = []
    right = []
    equal = []
    
    for product in products:
        product_primary = _get_sort_value(product, primary_sort)
        product_secondary = _get_sort_value(product, secondary_sort)
        
        # Compare primary field first
        if order == 'asc':
            if product_primary < pivot_primary:
                left.append(product)
            elif product_primary > pivot_primary:
                right.append(product)
            else:
                # Primary values are equal, compare secondary
                if product_secondary < pivot_secondary:
                    left.append(product)
                elif product_secondary > pivot_secondary:
                    right.append(product)
                else:
                    equal.append(product)
        else:  # desc
            if product_primary > pivot_primary:
                left.append(product)
            elif product_primary < pivot_primary:
                right.append(product)
            else:
                # Primary values are equal, compare secondary
                if product_secondary > pivot_secondary:
                    left.append(product)
                elif product_secondary < pivot_secondary:
                    right.append(product)
                else:
                    equal.append(product)
    
    # Recursively sort left and right partitions
    sorted_left = _hybrid_sort_recursive(left, primary_sort, secondary_sort, order)
    sorted_right = _hybrid_sort_recursive(right, primary_sort, secondary_sort, order)
    
    # Combine results
    return sorted_left + equal + sorted_right