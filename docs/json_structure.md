# TikTok JSON Structure

This document provides a high-level overview of the JSON structure provided
by a TikTok data export.

The export contains significantly more information than is required for this
project. Only sections relevant to personal usage and interest analytics are
documented in detail.

```text
root 
├── Ads and data
├── App Settings
├── Comment
├── Direct Message
├── Income Plus Wallet Transactions
├── Location Review
├── Post
├── Profile
├── TikTok Shop
├── Tiktok Live
└── Your Activity
```


### Activity Sections Used:
```text
Your Activity:
    ├── Activity Summary 
    ├── Collection
    ├── Favorite Collection
    ├── Favorite Comment
    ├── Favorite Effects
    ├── Favorite Hashtags
    ├── Favorite Location
    ├── Favorite Sounds
    ├── Favorite Videos
    ├── Like List
    ├── Login History  ⭐
    ├── Purchases
    ├── Searches
    └── Watch History ⭐
```