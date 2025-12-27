#!/usr/bin/env python3
"""
Naija-Rent-Estimator - The Rent Oracle
AI-Powered Rent Estimation for Lagos Apartments

Protects tenants from overpriced listings with:
- Fair price range calculation
- Greed Meter (flags overpriced apartments)
- Market trend analysis
- Tier-based comparison
"""

import json
from typing import Dict, Optional, Tuple
from pathlib import Path


class NaijaRentEstimator:
    """
    AI-powered rent estimation for Lagos apartments
    
    Features:
    - Predict fair rent based on location + bedrooms
    - Greed Meter: Detect overpriced listings
    - Market trend analysis
    - Tier comparison (Luxury, Premium, Mid-Range, Affordable, Budget)
    """
    
    def __init__(self, database_path: str = 'data/market_data.json'):
        """
        Initialize the rent estimator
        
        Args:
            database_path: Path to market data JSON
        """
        self.database_path = Path(database_path)
        self.market_data = {}
        self.areas_map = {}
        self.load_database()
        
        print("🏠 Naija-Rent-Estimator initialized")
        print(f"   Database: {len(self.areas_map)} Lagos areas loaded")
    
    def load_database(self):
        """Load the market data database"""
        if not self.database_path.exists():
            raise FileNotFoundError(f"Database not found: {self.database_path}")
        
        with open(self.database_path, 'r', encoding='utf-8') as f:
            self.market_data = json.load(f)
            
            # Build area lookup map (case-insensitive)
            for area in self.market_data.get('areas', []):
                area_name = area['name'].lower()
                self.areas_map[area_name] = area
    
    def predict_rent(
        self,
        location: str,
        bedrooms: int,
        asking_price: Optional[float] = None
    ) -> Dict:
        """
        Predict fair rent for an apartment
        
        Args:
            location: Area name (e.g., "Lekki Phase 1", "Yaba", "Ikeja")
            bedrooms: Number of bedrooms (1-4)
            asking_price: Optional asking price to check against market (enables Greed Meter)
            
        Returns:
            Dictionary with:
            {
                "location": Area name,
                "bedrooms": Number of bedrooms,
                "fair_range": {"min": X, "avg": Y, "max": Z},
                "market_trend": Trend description,
                "tier": Pricing tier,
                "amenities": List of typical amenities,
                "greed_meter": Greed analysis (if asking_price provided),
                "recommendation": Advice for tenant
            }
            
        Example:
            >>> estimator = NaijaRentEstimator()
            >>> result = estimator.predict_rent("Lekki Phase 1", 2, asking_price=2500000)
            >>> print(result['greed_meter']['verdict'])
            "Fair Price"
        """
        # Normalize location
        location_lower = location.lower().strip()
        
        # Find area
        area_data = self.areas_map.get(location_lower)
        if not area_data:
            return {
                "error": f"Location '{location}' not found",
                "available_locations": list(self.areas_map.keys()),
                "hint": "Try: Lekki Phase 1, Yaba, Ikeja, Victoria Island, Ikoyi"
            }
        
        # Validate bedrooms
        if bedrooms not in [1, 2, 3, 4]:
            return {
                "error": f"Invalid bedrooms count: {bedrooms}",
                "hint": "Supported: 1, 2, 3, or 4 bedrooms"
            }
        
        # Get pricing data
        bedroom_key = f"{bedrooms}_bedroom"
        pricing = area_data['pricing'].get(bedroom_key)
        
        if not pricing:
            return {
                "error": f"No data for {bedrooms}-bedroom in {area_data['name']}",
                "available_bedrooms": list(area_data['pricing'].keys())
            }
        
        # Build result
        result = {
            "location": area_data['name'],
            "lga": area_data['lga'],
            "bedrooms": bedrooms,
            "tier": area_data['tier'],
            "description": area_data['description'],
            "fair_range": {
                "min": pricing['min'],
                "avg": pricing['avg'],
                "max": pricing['max'],
                "formatted": self._format_price_range(pricing['min'], pricing['avg'], pricing['max'])
            },
            "market_trend": pricing['market_trend'],
            "amenities": area_data.get('amenities', []),
            "popular_estates": area_data.get('popular_estates', [])
        }
        
        # Add Greed Meter if asking price provided
        if asking_price is not None:
            result['asking_price'] = asking_price
            result['greed_meter'] = self._calculate_greed_meter(
                asking_price,
                pricing['min'],
                pricing['avg'],
                pricing['max']
            )
            result['recommendation'] = self._get_recommendation(result['greed_meter'])
        else:
            result['recommendation'] = f"Fair price range: {result['fair_range']['formatted']}"
        
        return result
    
    def _calculate_greed_meter(
        self,
        asking_price: float,
        min_price: float,
        avg_price: float,
        max_price: float
    ) -> Dict:
        """
        Calculate the Greed Meter for an asking price
        
        Args:
            asking_price: Landlord's asking price
            min_price: Market minimum
            avg_price: Market average
            max_price: Market maximum
            
        Returns:
            Dictionary with greed analysis
        """
        # Calculate percentage above/below average
        diff_from_avg = asking_price - avg_price
        percent_diff = (diff_from_avg / avg_price) * 100
        
        # Calculate percentage above max (for overpricing detection)
        if asking_price > max_price:
            percent_above_max = ((asking_price - max_price) / max_price) * 100
        else:
            percent_above_max = 0
        
        # Determine verdict
        if asking_price < min_price:
            verdict = "🎉 GREAT DEAL!"
            risk_level = "Low Risk"
            color = "green"
            emoji = "🎉"
        elif min_price <= asking_price <= max_price:
            verdict = "✅ FAIR PRICE"
            risk_level = "Low Risk"
            color = "green"
            emoji = "✅"
        elif percent_above_max <= 10:
            verdict = "⚠️ SLIGHTLY OVERPRICED"
            risk_level = "Moderate Risk"
            color = "yellow"
            emoji = "⚠️"
        elif 10 < percent_above_max <= 20:
            verdict = "🚨 OVERPRICED"
            risk_level = "High Risk"
            color = "orange"
            emoji = "🚨"
        elif 20 < percent_above_max <= 50:
            verdict = "🔥 EXTREME GREED"
            risk_level = "Very High Risk"
            color = "red"
            emoji = "🔥"
        else:
            verdict = "💀 HIGHWAY ROBBERY"
            risk_level = "AVOID"
            color = "red"
            emoji = "💀"
        
        # Build greed meter
        greed_meter = {
            "verdict": verdict,
            "risk_level": risk_level,
            "emoji": emoji,
            "color": color,
            "percent_diff_from_avg": round(percent_diff, 1),
            "percent_above_max": round(percent_above_max, 1) if percent_above_max > 0 else 0,
            "position": self._get_price_position(asking_price, min_price, avg_price, max_price),
            "greed_score": self._calculate_greed_score(asking_price, min_price, avg_price, max_price)
        }
        
        return greed_meter
    
    def _get_price_position(
        self,
        asking_price: float,
        min_price: float,
        avg_price: float,
        max_price: float
    ) -> str:
        """Get a text description of where the price sits in the range"""
        if asking_price < min_price:
            return "Below market minimum (unusual, check property condition)"
        elif asking_price < avg_price:
            return "Below average (good negotiation or lower-end property)"
        elif asking_price == avg_price:
            return "At market average (typical price)"
        elif asking_price <= max_price:
            return "Above average but within range (higher-end property or premium features)"
        else:
            percent_over = ((asking_price - max_price) / max_price) * 100
            return f"Above market maximum by {percent_over:.0f}% (likely overpriced)"
    
    def _calculate_greed_score(
        self,
        asking_price: float,
        min_price: float,
        avg_price: float,
        max_price: float
    ) -> int:
        """
        Calculate a greed score (0-100)
        0 = Great deal
        50 = Fair price
        100 = Extreme greed
        """
        if asking_price <= min_price:
            return 0
        elif asking_price <= avg_price:
            # 0-40 range
            ratio = (asking_price - min_price) / (avg_price - min_price)
            return int(ratio * 40)
        elif asking_price <= max_price:
            # 40-60 range
            ratio = (asking_price - avg_price) / (max_price - avg_price)
            return int(40 + (ratio * 20))
        else:
            # 60-100 range
            percent_above = ((asking_price - max_price) / max_price) * 100
            if percent_above >= 50:
                return 100
            else:
                return int(60 + (percent_above / 50 * 40))
    
    def _get_recommendation(self, greed_meter: Dict) -> str:
        """Get a recommendation based on greed meter verdict"""
        risk = greed_meter['risk_level']
        
        if risk == "Low Risk":
            return "✅ This is a fair price. You can proceed with confidence."
        elif risk == "Moderate Risk":
            return "⚠️ Slightly overpriced. Try negotiating down by 10-15%."
        elif risk == "High Risk":
            return "🚨 Overpriced! Negotiate hard or look for alternatives."
        elif risk == "Very High Risk":
            return "🔥 AVOID. This landlord is exploiting tenants. Look elsewhere."
        elif risk == "AVOID":
            return "💀 RUN! This is highway robbery. Report to authorities if necessary."
        else:
            return "Consult with a real estate agent."
    
    def _format_price_range(self, min_price: float, avg_price: float, max_price: float) -> str:
        """Format price range for display"""
        def format_naira(amount):
            if amount >= 1000000:
                return f"₦{amount/1000000:.1f}M"
            else:
                return f"₦{amount/1000:.0f}k"
        
        return f"{format_naira(min_price)} - {format_naira(max_price)} (avg: {format_naira(avg_price)})"
    
    def compare_tiers(self, bedrooms: int) -> Dict:
        """
        Compare prices across all tiers for a given bedroom count
        
        Args:
            bedrooms: Number of bedrooms
            
        Returns:
            Dictionary with tier comparison
        """
        comparison = {
            "bedrooms": bedrooms,
            "tiers": {}
        }
        
        # Group areas by tier
        tier_areas = {}
        for area_name, area_data in self.areas_map.items():
            tier = area_data['tier']
            bedroom_key = f"{bedrooms}_bedroom"
            pricing = area_data['pricing'].get(bedroom_key)
            
            if pricing:
                if tier not in tier_areas:
                    tier_areas[tier] = []
                
                tier_areas[tier].append({
                    "name": area_data['name'],
                    "avg_price": pricing['avg'],
                    "range": self._format_price_range(pricing['min'], pricing['avg'], pricing['max'])
                })
        
        # Sort by average price within each tier
        for tier, areas in tier_areas.items():
            tier_areas[tier] = sorted(areas, key=lambda x: x['avg_price'])
        
        comparison['tiers'] = tier_areas
        return comparison
    
    def format_result(self, result: Dict) -> str:
        """
        Format prediction result for display
        
        Args:
            result: Result from predict_rent()
            
        Returns:
            Formatted string
        """
        if 'error' in result:
            output = []
            output.append("=" * 70)
            output.append(f"❌ ERROR: {result['error']}")
            if 'hint' in result:
                output.append(f"💡 HINT: {result['hint']}")
            output.append("=" * 70)
            return '\n'.join(output)
        
        output = []
        output.append("=" * 70)
        output.append(f"🏠 NAIJA RENT ESTIMATOR - {result['location']}")
        output.append("=" * 70)
        output.append("")
        
        # Basic info
        output.append(f"📍 LOCATION: {result['location']} ({result['lga']} LGA)")
        output.append(f"🛏️  BEDROOMS: {result['bedrooms']}-bedroom apartment")
        output.append(f"🏆 TIER: {result['tier']}")
        output.append(f"📝 DESCRIPTION: {result['description']}")
        output.append("")
        
        # Fair price range
        output.append(f"💰 FAIR PRICE RANGE (Annual):")
        output.append(f"   Minimum: ₦{result['fair_range']['min']:,}")
        output.append(f"   Average: ₦{result['fair_range']['avg']:,}")
        output.append(f"   Maximum: ₦{result['fair_range']['max']:,}")
        output.append(f"   Summary: {result['fair_range']['formatted']}")
        output.append("")
        
        # Market trend
        output.append(f"📈 MARKET TREND: {result['market_trend']}")
        output.append("")
        
        # Amenities
        if result['amenities']:
            output.append(f"✨ TYPICAL AMENITIES: {', '.join(result['amenities'])}")
            output.append("")
        
        # Popular estates
        if result['popular_estates']:
            output.append(f"🏘️  POPULAR ESTATES: {', '.join(result['popular_estates'])}")
            output.append("")
        
        # Greed Meter (if asking price provided)
        if 'greed_meter' in result:
            gm = result['greed_meter']
            output.append(f"💵 ASKING PRICE: ₦{result['asking_price']:,}")
            output.append("")
            output.append("🔥 GREED METER ANALYSIS:")
            output.append(f"   Verdict: {gm['verdict']}")
            output.append(f"   Risk Level: {gm['risk_level']}")
            output.append(f"   Position: {gm['position']}")
            output.append(f"   Difference from Average: {gm['percent_diff_from_avg']:+.1f}%")
            if gm['percent_above_max'] > 0:
                output.append(f"   ⚠️  Above Maximum by: {gm['percent_above_max']:.1f}%")
            
            # Greed score bar
            greed_score = gm['greed_score']
            bar_length = 40
            filled = int((greed_score / 100) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            output.append(f"   Greed Score: {greed_score}/100 {bar}")
            output.append("")
        
        # Recommendation
        output.append(f"💡 RECOMMENDATION:")
        output.append(f"   {result['recommendation']}")
        
        output.append("")
        output.append("=" * 70)
        output.append("🏠 Naija-Rent-Estimator - Protecting tenants from overpriced listings")
        
        return '\n'.join(output)


def main():
    """Command-line interface"""
    import sys
    
    print("🏠 Naija-Rent-Estimator - The Rent Oracle")
    print("=" * 70)
    
    if len(sys.argv) < 3:
        print("\n📖 Usage:")
        print("  python estimator.py <location> <bedrooms> [asking_price]")
        print("\n💡 Examples:")
        print("  python estimator.py 'Lekki Phase 1' 2")
        print("  python estimator.py 'Yaba' 1 700000")
        print("  python estimator.py 'Victoria Island' 3 8000000")
        print("\n🗺️  Available Locations (15):")
        print("  • Luxury: Victoria Island, Ikoyi")
        print("  • Premium: Lekki Phase 1, Lekki Phase 2, Magodo")
        print("  • Mid-Range: Yaba, Ikeja, Surulere, Gbagada, Festac Town, Ojodu")
        print("  • Affordable: Ajah, Ikorodu, Isolo")
        print("  • Budget: Agege")
        return
    
    # Parse arguments
    location = sys.argv[1]
    try:
        bedrooms = int(sys.argv[2])
    except ValueError:
        print(f"\n❌ Error: Bedrooms must be a number (1-4)")
        return
    
    asking_price = None
    if len(sys.argv) >= 4:
        try:
            asking_price = float(sys.argv[3])
        except ValueError:
            print(f"\n❌ Error: Asking price must be a number")
            return
    
    # Initialize estimator
    try:
        estimator = NaijaRentEstimator()
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("Make sure data/market_data.json is in the same directory.")
        return
    
    print(f"\n🔍 Analyzing rent for {bedrooms}-bedroom in {location}...")
    print("=" * 70)
    
    # Predict rent
    result = estimator.predict_rent(location, bedrooms, asking_price)
    
    # Print formatted result
    print()
    print(estimator.format_result(result))


if __name__ == '__main__':
    main()
