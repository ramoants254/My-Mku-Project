# Nairobi Transportation System

A Django-based bus booking and transportation management system for Nairobi routes.

## Models Overview

### Route
- Manages bus routes with start and end points
- Stores fare information for each route
- Fields: start_point, end_point, fare

### Bus
- Represents individual buses in the system
- Links to specific routes
- Tracks capacity, location, and schedule
- Fields: route, capacity, current_location, departure_time, date

### Seat
- Manages individual seats within buses
- Tracks booking status
- Fields: bus, seat_label, is_booked

### Booking
- Handles user bookings
- Implements atomic transactions for seat booking
- Fields: user, seat, date, payment

### Payment
- Manages payment transactions
- Tracks payment status (Pending, Success, Failed)
- Fields: user, amount, transaction_id, status, created_at

### Feedback
- Allows users to provide feedback and ratings
- Fields: user, message, rating, created_at

## Key Features

1. **Route Management**
   - Define bus routes
   - Set fare prices

2. **Bus Scheduling**
   - Schedule buses for specific routes
   - Track bus capacity and location

3. **Seat Booking**
   - Atomic booking transactions
   - Automatic seat status management
   - Prevents double booking

4. **Payment Processing**
   - Track payment status
   - Link payments to bookings

5. **User Feedback**
   - Rating system (1-5 stars)
   - User feedback collection

## Technical Details

- Built with Django
- Uses atomic transactions for booking operations
- Implements data validation (e.g., future date validation)
- Follows Django's model relationships best practices

## Database Relationships

- Route → Bus (One-to-Many)
- Bus → Seat (One-to-Many)
- User → Booking (One-to-Many)
- Booking → Payment (One-to-One)
- User → Feedback (One-to-Many)

## Usage Notes

1. All dates must be in the future for bus scheduling
2. Seat bookings are handled atomically to prevent conflicts
3. Payments are tracked with unique transaction IDs
4. Bus capacity defaults to 36 seats
5. Feedback includes ratings from 1 to 5 