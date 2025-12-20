'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';

interface Vendor {
  id: number;
  business_name: string;
  office_city: string;
  office_state: string;
  office_country: string;
  latitude: string;
  longitude: string;
  product_count: number;
}

interface LocationMapFilterProps {
  onLocationSelect: (location: { city?: string; state?: string; country?: string; lat?: number; lng?: number; radius?: number }) => void;
  selectedLocation: any;
}

export default function LocationMapFilter({ onLocationSelect, selectedLocation }: LocationMapFilterProps) {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCity, setSelectedCity] = useState('');
  const [selectedState, setSelectedState] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('');
  const [useRadius, setUseRadius] = useState(false);
  const [radius, setRadius] = useState(50);

  useEffect(() => {
    fetchVendorLocations();
  }, []);

  const fetchVendorLocations = async () => {
    try {
      const response = await api.get('/products/vendor-locations/');
      setVendors(response.data);
    } catch (error) {
      console.error('Error fetching vendor locations:', error);
    } finally {
      setLoading(false);
    }
  };

  // Get unique cities, states, and countries
  const cities = Array.from(new Set(vendors.map(v => v.office_city).filter(Boolean))).sort();
  const states = Array.from(new Set(vendors.map(v => v.office_state).filter(Boolean))).sort();
  const countries = Array.from(new Set(vendors.map(v => v.office_country).filter(Boolean))).sort();

  const handleApplyFilter = () => {
    const filter: any = {};
    
    if (selectedCity) filter.city = selectedCity;
    if (selectedState) filter.state = selectedState;
    if (selectedCountry) filter.country = selectedCountry;
    
    // If using radius search, find the first vendor in selected location
    if (useRadius && (selectedCity || selectedState)) {
      const vendor = vendors.find(v => 
        (!selectedCity || v.office_city === selectedCity) &&
        (!selectedState || v.office_state === selectedState)
      );
      
      if (vendor) {
        filter.lat = parseFloat(vendor.latitude);
        filter.lng = parseFloat(vendor.longitude);
        filter.radius = radius;
      }
    }
    
    onLocationSelect(filter);
  };

  const handleClearFilter = () => {
    setSelectedCity('');
    setSelectedState('');
    setSelectedCountry('');
    setUseRadius(false);
    onLocationSelect({});
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-bold flex items-center gap-2">
          <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Filter by Location
        </h3>
        <span className="text-sm text-gray-600">
          {vendors.length} vendors with locations
        </span>
      </div>

      {loading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-2 text-sm text-gray-600">Loading locations...</p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Country Filter */}
          <div>
            <label className="block text-sm font-medium mb-2">Country</label>
            <select
              value={selectedCountry}
              onChange={(e) => {
                setSelectedCountry(e.target.value);
                setSelectedState('');
                setSelectedCity('');
              }}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
            >
              <option value="">All Countries</option>
              {countries.map(country => (
                <option key={country} value={country}>
                  {country} ({vendors.filter(v => v.office_country === country).length})
                </option>
              ))}
            </select>
          </div>

          {/* State/Region Filter */}
          <div>
            <label className="block text-sm font-medium mb-2">State/Region</label>
            <select
              value={selectedState}
              onChange={(e) => {
                setSelectedState(e.target.value);
                setSelectedCity('');
              }}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
              disabled={!selectedCountry && states.length > 20}
            >
              <option value="">All States/Regions</option>
              {states
                .filter(state => !selectedCountry || vendors.some(v => v.office_state === state && v.office_country === selectedCountry))
                .map(state => (
                  <option key={state} value={state}>
                    {state} ({vendors.filter(v => v.office_state === state && (!selectedCountry || v.office_country === selectedCountry)).length})
                  </option>
                ))}
            </select>
          </div>

          {/* City Filter */}
          <div>
            <label className="block text-sm font-medium mb-2">City</label>
            <select
              value={selectedCity}
              onChange={(e) => setSelectedCity(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
              disabled={!selectedState && cities.length > 50}
            >
              <option value="">All Cities</option>
              {cities
                .filter(city => 
                  (!selectedState || vendors.some(v => v.office_city === city && v.office_state === selectedState)) &&
                  (!selectedCountry || vendors.some(v => v.office_city === city && v.office_country === selectedCountry))
                )
                .map(city => (
                  <option key={city} value={city}>
                    {city} ({vendors.filter(v => 
                      v.office_city === city && 
                      (!selectedState || v.office_state === selectedState) &&
                      (!selectedCountry || v.office_country === selectedCountry)
                    ).length})
                  </option>
                ))}
            </select>
          </div>

          {/* Radius Search Option */}
          {(selectedCity || selectedState) && (
            <div className="border-t pt-4">
              <label className="flex items-center gap-2 mb-3">
                <input
                  type="checkbox"
                  checked={useRadius}
                  onChange={(e) => setUseRadius(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm font-medium">Search within radius</span>
              </label>
              
              {useRadius && (
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Radius: {radius} km
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="200"
                    step="10"
                    value={radius}
                    onChange={(e) => setRadius(parseInt(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>10 km</span>
                    <span>200 km</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Location Summary */}
          {(selectedCity || selectedState || selectedCountry) && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm font-medium text-blue-900 mb-1">Selected Location:</p>
              <p className="text-sm text-blue-700">
                {[selectedCity, selectedState, selectedCountry].filter(Boolean).join(', ')}
              </p>
              {useRadius && (
                <p className="text-xs text-blue-600 mt-1">
                  Within {radius} km radius
                </p>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={handleApplyFilter}
              disabled={!selectedCity && !selectedState && !selectedCountry}
              className="flex-1 bg-primary text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              Apply Location Filter
            </button>
            <button
              onClick={handleClearFilter}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              Clear
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
