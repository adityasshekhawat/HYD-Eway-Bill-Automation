. Data Structure & Routing:
From/To filtering: Does each row in Raw_DC.csv have origin/destination info? Or do we need to infer this from hub addresses? - So in our Raw_DC file From field is indicated by "name" column and To is indicated by column "hub"
FC Arihant: Is this a fixed origin for all trips, or can it vary?  - It can't vary for our v1 but later on we will scale this system for PAN India
2. Trip Grouping Logic:
Constraints: Any business rules for which trips can be grouped together? (same destination hub, weight limits, product types?) - same destination is the only filter to extract trip_id's
Mixed senders: Can one vehicle carry products from all 3 senders (Amolakchand, SourcingBee, Bodega)? - Yes, you need to understand these are name of sellers not senders, sender is either Arihant or other FC name, and receiver is hub, so for each vehicle there will be 3 trips to Amolakchand, SourcingBee and Bodega
3. DC Generation:
Product consolidation: When multiple trips are grouped, do we:
Combine all products from all trips into single DCs per sender? -Yes
Keep trip-wise breakdown within each DC? - NO, you can combine all, only rule is we can't have more than 250 line items in one DC, if we have let's say 300 products in a DC, then we will have to split it into 2 DCs tagged to same Serial No. of DC

Vehicle number: Cell I4 is currently empty - this will now show the assigned vehicle number? - Yes, this is purely based on users input

4. Frontend Workflow:
Trip selection: Multiple selection checkbox/dropdown? - Check Box

Vehicle assignment: Manual input field or auto-generation? - Manual Input

Validation: Any checks needed (weight, volume, route compatibility)? - No

5. Data Output:
File naming: Still include trip info or switch to vehicle-based naming? -Switch to Vehicle Number

Audit trail: Need to track which trips went into which vehicle? - Yes, that would be great

Am I understanding the core concept correctly? The main shift is from "3 DCs per trip" to "3 DCs per vehicle (containing multiple trips)"? - Yes