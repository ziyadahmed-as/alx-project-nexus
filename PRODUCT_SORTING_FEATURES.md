# Product Sorting and Display Features

## Overview
Enhanced product display system that prioritizes featured products and new arrivals, providing better visibility for quality products and fresh inventory.

## Features Implemented

### 1. Smart Product Ordering (Backend)
**File:** `backend/apps/products/views.py`

**Default Sorting:**
```python
.order_by(
    '-featured',   # Featured products first
    '-created_at'  # Then newest products
)
```

**Benefits:**
- Featured products always appear first
- New products get priority visibility
- Encourages vendors to maintain fresh inventory
- Rewards quality products with featured status

### 2. Home Page Sections (Frontend)
**File:** `frontend/src/app/page.tsx`

**Sections:**

#### Featured Products Section
- Shows products marked as "featured" by admin
- Highlighted with yellow/orange gradient banner
- Star icon and special styling
- "View All" link to filtered page
- Limited to 8 products

#### New Arrivals Section
- Shows newest products (sorted by creation date)
- Highlighted with green/blue gradient banner
- "New" icon and special styling
- "View All" link to products page
- Limited to 8 products

#### Shop by Category
- Quick access to product categories
- Visual category cards with emojis
- Direct links to filtered views

### 3. Products Listing Page
**File:** `frontend/src/app/products/page.tsx`

**Sorting Options:**
- **Featured First** - Shows featured products at top
- **Newest First** - Shows recently added products
- **Most Popular** - Sorts by sales count
- **Price: Low to High** - Budget-friendly first
- **Price: High to Low** - Premium products first

**Quick Filters:**
- Featured button (yellow badge)
- New Arrivals button (green badge)
- Popular button (blue badge)

### 4. Enhanced Product Cards
**File:** `frontend/src/components/ProductCard.tsx`

**Visual Indicators:**

#### Featured Badge
```
⭐ Featured
Yellow background, top-left corner
```

#### New Badge
```
🆕 New
Green background, top-left corner
Shows for products < 7 days old
```

#### Discount Badge
```
-XX%
Red background, top-right corner
Calculated from compare_price
```

**Additional Enhancements:**
- Stock status indicator
- Compare price (strikethrough)
- Vendor name
- Improved layout and spacing
- Better hover effects

## User Experience

### For Buyers

#### Home Page Experience
1. **First Impression:** Featured products immediately visible
2. **Discovery:** New arrivals section shows fresh inventory
3. **Navigation:** Category cards for quick browsing
4. **Visual Cues:** Badges help identify special products

#### Products Page Experience
1. **Sorting Control:** Dropdown to change sort order
2. **Quick Filters:** One-click access to featured/new/popular
3. **Visual Feedback:** Active filter highlighted
4. **Product Count:** Shows number of products found

#### Product Card Experience
1. **Instant Recognition:** Badges show product status
2. **Price Comparison:** See original price and discount
3. **Stock Awareness:** Know availability before clicking
4. **Quick Action:** Add to cart without leaving page

### For Vendors

#### Benefits of Featured Status
- **Top Placement:** Product appears first in listings
- **Visual Badge:** Yellow star badge attracts attention
- **Home Page:** Included in featured section
- **Increased Sales:** Better visibility = more conversions

#### Benefits of New Products
- **Automatic Priority:** New products get top placement
- **7-Day Window:** Badge shows for first week
- **Fresh Inventory:** Encourages regular product additions
- **Discovery:** Buyers actively look for new items

### For Admins

#### Product Management
- Mark products as "featured" to promote quality items
- Featured status gives vendors incentive for quality
- Can be used as reward for good vendors
- Helps curate marketplace experience

## Technical Implementation

### Backend Ordering

```python
# Default queryset ordering
Product.objects.filter(
    is_active=True, 
    status='published'
).order_by(
    '-featured',    # Boolean: True comes before False
    '-created_at'   # DateTime: Newest first
)
```

### Frontend Sorting

```typescript
// Sort options mapping
switch (sortBy) {
  case 'newest':
    params.append('ordering', '-created_at');
    break;
  case 'price-low':
    params.append('ordering', 'price');
    break;
  case 'price-high':
    params.append('ordering', '-price');
    break;
  case 'popular':
    params.append('ordering', '-sales_count');
    break;
  case 'featured':
    params.append('ordering', '-featured,-created_at');
    break;
}
```

### New Product Detection

```typescript
// Check if product is new (< 7 days old)
const isNew = product.created_at 
  ? new Date().getTime() - new Date(product.created_at).getTime() < 7 * 24 * 60 * 60 * 1000
  : false;
```

## Configuration

### Adjustable Parameters

#### New Product Duration
**Location:** `frontend/src/components/ProductCard.tsx`
```typescript
// Change 7 to desired number of days
< 7 * 24 * 60 * 60 * 1000
```

#### Products Per Section
**Location:** `frontend/src/app/page.tsx`
```typescript
// Change 8 to desired number
setFeaturedProducts(featured.slice(0, 8));
setNewProducts(newest.slice(0, 8));
```

#### Default Sort Order
**Location:** `frontend/src/app/products/page.tsx`
```typescript
// Change default sort
const [sortBy, setSortBy] = useState('newest');
```

## API Endpoints

### Get Products (Sorted)
```
GET /api/products/
Query Parameters:
  - ordering: -featured,-created_at (default)
  - ordering: -created_at (newest)
  - ordering: price (low to high)
  - ordering: -price (high to low)
  - ordering: -sales_count (popular)
  - featured: true (featured only)
  - category: <category_id>
```

### Response Format
```json
{
  "results": [
    {
      "id": 1,
      "name": "Product Name",
      "price": "99.99",
      "compare_price": "129.99",
      "featured": true,
      "created_at": "2024-01-15T10:30:00Z",
      "stock": 50,
      "images": [...],
      "vendor_name": "Vendor Name"
    }
  ]
}
```

## SEO Benefits

### Improved Rankings
- Fresh content (new products) signals active site
- Featured products can be optimized for keywords
- Better user engagement metrics
- Lower bounce rates

### Structured Data
Consider adding:
```json
{
  "@type": "Product",
  "offers": {
    "availability": "InStock",
    "priceValidUntil": "...",
    "itemCondition": "NewCondition"
  }
}
```

## Analytics Tracking

### Recommended Events
```javascript
// Track featured product views
gtag('event', 'view_featured_product', {
  product_id: product.id,
  product_name: product.name
});

// Track new product views
gtag('event', 'view_new_product', {
  product_id: product.id,
  days_since_creation: daysSinceCreation
});

// Track sort changes
gtag('event', 'change_sort', {
  sort_type: sortBy
});
```

## Performance Considerations

### Database Indexing
Ensure indexes on:
```python
# In Product model
class Meta:
    indexes = [
        models.Index(fields=['-featured', '-created_at']),
        models.Index(fields=['-created_at']),
        models.Index(fields=['price']),
        models.Index(fields=['-sales_count']),
    ]
```

### Caching Strategy
```python
# Cache featured products (changes rarely)
featured_products = cache.get_or_set(
    'featured_products',
    lambda: Product.objects.filter(featured=True)[:8],
    timeout=3600  # 1 hour
)
```

## Future Enhancements

### Potential Features
1. **Trending Products:** Based on recent views/sales
2. **Personalized Sorting:** Based on user preferences
3. **Time-Based Promotions:** Flash sales, daily deals
4. **Seasonal Collections:** Holiday-specific products
5. **Vendor Spotlight:** Rotate featured vendors
6. **Smart Recommendations:** AI-based suggestions
7. **Recently Viewed:** Show user's browsing history
8. **Wishlist Integration:** Sort by wishlisted items

### Advanced Sorting
1. **Multi-criteria Sort:** Combine multiple factors
2. **Relevance Score:** Calculate based on multiple metrics
3. **User Behavior:** Learn from click patterns
4. **A/B Testing:** Test different sort algorithms
5. **Geographic Sorting:** Prioritize local vendors

## Testing

### Test Cases

#### Test 1: Featured Products Display
```
1. Mark product as featured in admin
2. Visit home page
3. Verify product appears in Featured section
4. Verify yellow star badge visible
5. Verify product appears first in listings
```

#### Test 2: New Products Display
```
1. Create new product
2. Visit home page
3. Verify product appears in New Arrivals
4. Verify green "New" badge visible
5. Wait 8 days
6. Verify badge no longer shows
```

#### Test 3: Sorting Functionality
```
1. Go to products page
2. Select "Price: Low to High"
3. Verify products sorted by price ascending
4. Select "Newest First"
5. Verify products sorted by date descending
```

#### Test 4: Badge Display
```
1. Create product with compare_price
2. Mark as featured
3. View product card
4. Verify featured badge shows
5. Verify new badge shows (if < 7 days)
6. Verify discount badge shows
```

## Troubleshooting

### Issue: Featured products not showing first
**Solution:** Check database query ordering in ProductListView

### Issue: New badge not appearing
**Solution:** Verify created_at field is set and < 7 days old

### Issue: Sorting not working
**Solution:** Check API query parameters and backend ordering_fields

### Issue: Badges overlapping
**Solution:** Adjust CSS positioning in ProductCard component

## Related Documentation

- `DRAFT_SYSTEM.md` - Product publishing system
- `VENDOR_SELF_PURCHASE_PREVENTION.md` - Purchase restrictions
- `README.md` - General project documentation

## Support

For issues or questions:
- Check browser console for errors
- Verify API responses in Network tab
- Check backend logs for query issues
- Contact support if problem persists
