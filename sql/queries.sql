-- Banggood Product Analysis SQL Queries

-- 1. Average Price per Category
SELECT 
    Category,
    AVG(Price) AS AveragePrice,
    COUNT(*) AS ProductCount
FROM Banggood_Products
WHERE Price IS NOT NULL
GROUP BY Category
ORDER BY AveragePrice DESC;

-- 2. Average Rating per Category
SELECT 
    Category,
    AVG(Rating) AS AverageRating,
    COUNT(*) AS ProductCount
FROM Banggood_Products
WHERE Rating IS NOT NULL AND Rating > 0
GROUP BY Category
ORDER BY AverageRating DESC;

-- 3. Product Count per Category
SELECT 
    Category,
    COUNT(*) AS ProductCount
FROM Banggood_Products
GROUP BY Category
ORDER BY ProductCount DESC;

-- 4. Top 10 Reviewed Products
SELECT TOP 10
    ProductName,
    Category,
    Price,
    Rating,
    ReviewCount,
    IsHighValue,
    ProductURL
FROM Banggood_Products
WHERE ReviewCount > 0
ORDER BY ReviewCount DESC;

-- 5. Price Range Count
SELECT 
    CASE 
        WHEN Price < 20 THEN 'Cheap'
        WHEN Price >= 20 AND Price <= 50 THEN 'Medium'
        WHEN Price > 50 THEN 'Expensive'
        ELSE 'Unknown'
    END AS PriceRange,
    COUNT(*) AS ProductCount
FROM Banggood_Products
WHERE Price IS NOT NULL
GROUP BY 
    CASE 
        WHEN Price < 20 THEN 'Cheap'
        WHEN Price >= 20 AND Price <= 50 THEN 'Medium'
        WHEN Price > 50 THEN 'Expensive'
        ELSE 'Unknown'
    END
ORDER BY 
    CASE 
        WHEN PriceRange = 'Cheap' THEN 1
        WHEN PriceRange = 'Medium' THEN 2
        WHEN PriceRange = 'Expensive' THEN 3
        ELSE 4
    END;

-- Additional useful queries

-- High Value Products (IsHighValue = 1)
SELECT 
    Category,
    COUNT(*) AS HighValueCount,
    AVG(Price) AS AvgPrice,
    AVG(Rating) AS AvgRating
FROM Banggood_Products
WHERE IsHighValue = 1
GROUP BY Category
ORDER BY HighValueCount DESC;

-- Products with Best Price per Review Ratio
SELECT TOP 20
    ProductName,
    Category,
    Price,
    ReviewCount,
    PricePerReview,
    Rating
FROM Banggood_Products
WHERE ReviewCount > 0 AND PricePerReview IS NOT NULL
ORDER BY PricePerReview ASC;

-- Category Performance Summary
SELECT 
    Category,
    COUNT(*) AS TotalProducts,
    AVG(Price) AS AvgPrice,
    AVG(Rating) AS AvgRating,
    SUM(ReviewCount) AS TotalReviews,
    SUM(CASE WHEN IsHighValue = 1 THEN 1 ELSE 0 END) AS HighValueCount
FROM Banggood_Products
GROUP BY Category
ORDER BY TotalProducts DESC;

