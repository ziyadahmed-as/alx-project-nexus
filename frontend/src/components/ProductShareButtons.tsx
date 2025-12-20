'use client';

import { useState } from 'react';
import toast from 'react-hot-toast';

interface ProductShareButtonsProps {
  productId: number;
  productName: string;
  productDescription: string;
  productImage?: string;
  productPrice: number;
}

export default function ProductShareButtons({
  productId,
  productName,
  productDescription,
  productImage,
  productPrice,
}: ProductShareButtonsProps) {
  const [showShareModal, setShowShareModal] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);

  // Generate the product URL
  const productUrl = typeof window !== 'undefined' 
    ? `${window.location.origin}/products/${productId}`
    : '';

  // Generate share text
  const shareText = `Check out ${productName} - Only $${productPrice}! ${productDescription.substring(0, 100)}...`;

  // Copy link to clipboard
  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(productUrl);
      setCopiedLink(true);
      toast.success('Link copied to clipboard!');
      setTimeout(() => setCopiedLink(false), 3000);
    } catch (error) {
      toast.error('Failed to copy link');
    }
  };

  // Share to Facebook
  const shareToFacebook = () => {
    const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(productUrl)}&quote=${encodeURIComponent(shareText)}`;
    window.open(facebookUrl, '_blank', 'width=600,height=400');
  };

  // Share to Instagram (opens Instagram with copied link)
  const shareToInstagram = () => {
    copyToClipboard();
    toast.success('Link copied! Open Instagram app and paste in your story or post', {
      duration: 5000,
    });
    // Instagram doesn't have a direct web share API, so we guide users
    setTimeout(() => {
      window.open('https://www.instagram.com/', '_blank');
    }, 1000);
  };

  // Share to TikTok with dashboard link
  const shareToTikTok = async () => {
    try {
      // Fetch the special TikTok dashboard link from backend
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/products/${productId}/tiktok-link/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        // Copy the special TikTok dashboard link
        await navigator.clipboard.writeText(data.tiktok_dashboard_link);
        
        toast.success(
          <div>
            <p className="font-bold">TikTok Dashboard Link Copied!</p>
            <p className="text-sm">Paste this link in your TikTok video description</p>
            <p className="text-xs mt-1">Suggested hashtags: #{data.hashtags.join(' #')}</p>
          </div>,
          { duration: 7000 }
        );
        
        // Track the share
        await fetch(`${process.env.NEXT_PUBLIC_API_URL}/products/${productId}/share/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: JSON.stringify({ platform: 'tiktok' }),
        });
        
        // Open TikTok after a delay
        setTimeout(() => {
          window.open('https://www.tiktok.com/', '_blank');
        }, 1500);
      } else {
        // Fallback to regular link if API fails
        copyToClipboard();
        toast.success('Link copied! Open TikTok app and paste in your video description', {
          duration: 5000,
        });
        setTimeout(() => {
          window.open('https://www.tiktok.com/', '_blank');
        }, 1000);
      }
    } catch (error) {
      // Fallback to regular link on error
      copyToClipboard();
      toast.success('Link copied! Open TikTok app and paste in your video description', {
        duration: 5000,
      });
      setTimeout(() => {
        window.open('https://www.tiktok.com/', '_blank');
      }, 1000);
    }
  };

  // Share to Telegram
  const shareToTelegram = () => {
    const telegramUrl = `https://t.me/share/url?url=${encodeURIComponent(productUrl)}&text=${encodeURIComponent(shareText)}`;
    window.open(telegramUrl, '_blank', 'width=600,height=400');
  };

  // Share to WhatsApp
  const shareToWhatsApp = () => {
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(shareText + ' ' + productUrl)}`;
    window.open(whatsappUrl, '_blank', 'width=600,height=400');
  };

  // Share to Twitter/X
  const shareToTwitter = () => {
    const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(productUrl)}`;
    window.open(twitterUrl, '_blank', 'width=600,height=400');
  };

  return (
    <>
      {/* Share Button */}
      <button
        onClick={() => setShowShareModal(true)}
        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
        </svg>
        Share Product
      </button>

      {/* Share Modal */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold">Share Product</h3>
              <button
                onClick={() => setShowShareModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Product Preview */}
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <p className="font-medium text-sm">{productName}</p>
              <p className="text-sm text-gray-600">${productPrice}</p>
            </div>

            {/* Copy Link */}
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Product Link</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={productUrl}
                  readOnly
                  className="flex-1 px-3 py-2 border rounded-lg text-sm bg-gray-50"
                />
                <button
                  onClick={copyToClipboard}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    copiedLink
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {copiedLink ? 'Copied!' : 'Copy'}
                </button>
              </div>
            </div>

            {/* Social Media Buttons */}
            <div className="space-y-2">
              <p className="text-sm font-medium mb-3">Share on Social Media</p>
              
              {/* Facebook */}
              <button
                onClick={shareToFacebook}
                className="w-full flex items-center gap-3 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                </svg>
                Share on Facebook
              </button>

              {/* Instagram */}
              <button
                onClick={shareToInstagram}
                className="w-full flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 text-white rounded-lg hover:opacity-90 transition-opacity"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                </svg>
                Share on Instagram
              </button>

              {/* TikTok */}
              <button
                onClick={shareToTikTok}
                className="w-full flex items-center gap-3 px-4 py-3 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
                </svg>
                Share on TikTok
              </button>

              {/* Telegram */}
              <button
                onClick={shareToTelegram}
                className="w-full flex items-center gap-3 px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                </svg>
                Share on Telegram
              </button>

              {/* WhatsApp */}
              <button
                onClick={shareToWhatsApp}
                className="w-full flex items-center gap-3 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
                </svg>
                Share on WhatsApp
              </button>

              {/* Twitter/X */}
              <button
                onClick={shareToTwitter}
                className="w-full flex items-center gap-3 px-4 py-3 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
                Share on X (Twitter)
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
