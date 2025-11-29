# Vendor Self-Purchase Prevention Feature

## Overview
This feature prevents vendors from purchasing their own products, which is a common e-commerce best practice to:
- Prevent fraudulent orders and inflated sales numbers
- Avoid fake reviews from product owners
- Maintain marketplace integrity
- Prevent manipulation of product rankings

## Implementation

### Frontend Protection

#### 1. Product Detail Page
**File:** `frontend/src/app/products/[id]/page.tsx`

**Features:**
- Detects if the logged-in user is the product owner
- Hides "Add to Cart" and "Buy Now" buttons for own products
- Shows informative message with "Edit Product" button instead
- Prevents cart addition even if buttons are somehow accessed

**Detection Logic:**
```typescript
// Check if current user is the product owner
if (isAuthenticated && user && user.role === 'vendor') {
  const vendorProfile = await api.get('/vendors/profile/');
  if (vendorProfile.data.id === product.vendor) {
    setIsOwnProduct(true);
  }
}
```

**UI Changes:**
- **For Own Products:** Shows blue info box with message and "Edit Product" button
- **For Other Products:** Shows normal "Add to Cart" and "Buy Now" buttons

#### 2. Cart Store Protection
**File:** `frontend/src/store/cartStore.ts`

**Features:**
- Added `vendorId` field to CartItem interface
- Can be extended to validate items before checkout

### Backend Protection

#### Order Creation Validation
**File:** `backend/apps/orders/views.py`

**Features:**
- Validates each product in the order
- Checks if vendor is trying to purchase their own product
- Returns error before creating order
- Prevents database manipulation

**Validation Logic:**
```python
if request.user.role == 'vendor':
    vendor_profile = request.user.vendor_profile
    for item_data in order_data['items']:
        product = Product.objects.get(id=item_data['product_id'])
        if product.vendor == vendor_profile:
            raise ValidationError({
                'detail': f'You cannot purchase your own product: {product.name}'
            })
```

## User Experience

### Scenario 1: Vendor Views Own Product

1. Vendor logs in and navigates to their product
2. Instead of purchase buttons, they see:
   ```
   ℹ️ This is Your Product
   
   You cannot purchase your own products. You can edit or 
   manage this product from your vendor dashboard.
   
   [Edit Product]
   ```
3. Clicking "Edit Product" redirects to product edit page

### Scenario 2: Vendor Tries to Add Own Product to Cart

1. If vendor somehow triggers add to cart (e.g., via API)
2. Toast notification appears: "You cannot purchase your own products!"
3. Product is not added to cart

### Scenario 3: Vendor Tries to Checkout with Own Product

1. If vendor bypasses frontend checks and submits order
2. Backend validation catches it
3. Returns error: "You cannot purchase your own product: [Product Name]"
4. Order is not created
5. Stock is not reduced

### Scenario 4: Regular Buyer Views Product

1. Buyer sees normal product page
2. "Add to Cart" and "Buy Now" buttons are visible
3. Can purchase normally

## Security Layers

### Layer 1: UI Prevention (Frontend)
- Hides purchase buttons for own products
- Shows informative message
- Provides alternative action (Edit Product)

### Layer 2: Action Prevention (Frontend)
- Blocks add to cart action in handler
- Shows error toast if attempted
- Prevents cart state modification

### Layer 3: API Validation (Backend)
- Validates order items before creation
- Checks product ownership
- Returns validation error
- Prevents order creation

## Edge Cases Handled

### 1. Vendor with Multiple Products
- Each product is checked individually
- Can purchase other vendors' products
- Cannot purchase any of their own products

### 2. Vendor Becomes Buyer
- If vendor role changes, restrictions are removed
- Based on current role at time of purchase

### 3. Product Ownership Transfer
- If product vendor changes, new owner cannot purchase
- Previous owner can now purchase

### 4. Admin Users
- Admins can purchase any product (including vendor products)
- No restrictions for admin role

### 5. Unauthenticated Users
- Can view all products normally
- Must login to purchase
- Restrictions apply after login if vendor

## Testing

### Test Case 1: Vendor Views Own Product
```
1. Login as vendor
2. Navigate to own product
3. Verify: No purchase buttons shown
4. Verify: Info message displayed
5. Verify: "Edit Product" button present
```

### Test Case 2: Vendor Attempts Cart Addition
```
1. Login as vendor
2. Try to add own product via console/API
3. Verify: Error toast appears
4. Verify: Product not in cart
```

### Test Case 3: Vendor Attempts Checkout
```
1. Login as vendor
2. Bypass frontend and POST order with own product
3. Verify: Backend returns 400 error
4. Verify: Order not created
5. Verify: Stock unchanged
```

### Test Case 4: Buyer Purchases Vendor Product
```
1. Login as buyer
2. Navigate to vendor's product
3. Verify: Purchase buttons visible
4. Add to cart successfully
5. Complete checkout successfully
```

### Test Case 5: Vendor Purchases Other Vendor Product
```
1. Login as vendor
2. Navigate to another vendor's product
3. Verify: Purchase buttons visible
4. Add to cart successfully
5. Complete checkout successfully
```

## API Endpoints Affected

### GET /api/products/{id}/
- Returns product details
- Frontend uses to check ownership

### GET /api/vendors/profile/
- Returns current user's vendor profile
- Used to compare with product vendor

### POST /api/orders/create/
- Creates new order
- Validates product ownership
- Returns error if vendor owns product

## Error Messages

### Frontend Errors
```javascript
// Cart addition attempt
"You cannot purchase your own products!"

// Info message on product page
"You cannot purchase your own products. You can edit or 
manage this product from your vendor dashboard."
```

### Backend Errors
```json
{
  "detail": "You cannot purchase your own product: [Product Name]"
}
```

## Configuration

No configuration needed. Feature is always active for vendor users.

## Future Enhancements

### Potential Improvements:
1. **Bulk Order Validation:** Check all cart items at once
2. **Warning on Cart Page:** Show warning if cart contains own products
3. **Analytics:** Track attempted self-purchases for fraud detection
4. **Admin Override:** Allow admins to enable self-purchase for testing
5. **Gift Purchases:** Allow vendors to purchase own products as gifts
6. **Wholesale Exception:** Allow vendors to purchase own products at cost

### Suggested Features:
1. **Self-Review Prevention:** Prevent vendors from reviewing own products
2. **Self-Rating Prevention:** Prevent vendors from rating own products
3. **Wishlist Restriction:** Prevent adding own products to wishlist
4. **Comparison Restriction:** Prevent comparing own products

## Benefits

### For Marketplace:
- ✅ Maintains integrity and trust
- ✅ Prevents sales manipulation
- ✅ Ensures authentic reviews
- ✅ Protects ranking algorithms

### For Vendors:
- ✅ Clear indication of own products
- ✅ Quick access to edit product
- ✅ Prevents accidental self-purchase
- ✅ Professional marketplace experience

### For Buyers:
- ✅ Authentic sales numbers
- ✅ Genuine reviews
- ✅ Fair product rankings
- ✅ Trustworthy marketplace

## Compliance

This feature helps comply with:
- E-commerce best practices
- Marketplace integrity standards
- Anti-fraud regulations
- Consumer protection laws

## Troubleshooting

### Issue: Vendor can still see purchase buttons
**Solution:** Clear browser cache and reload page

### Issue: Error when viewing own product
**Solution:** Ensure vendor profile is properly set up

### Issue: Cannot purchase any products
**Solution:** Check user role - may be incorrectly set as vendor

### Issue: Backend validation not working
**Solution:** Ensure vendor profile relationship is correct

## Related Documentation

- `DRAFT_SYSTEM.md` - Product draft and publishing system
- `AUTO_DASHBOARD_REDIRECT.md` - Role-based dashboard routing
- `README.md` - General project documentation

## Support

For issues related to this feature:
1. Check error messages in browser console
2. Check backend logs for validation errors
3. Verify user role and vendor profile
4. Contact support if issue persists
