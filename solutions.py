# automatisch aus solutions.xlsx generiert
SOLUTIONS = {
    'g1_task1_w2': """
def clean_reading_list(reading_list):
    cleaned = {}
    
    for user, books in reading_list.items():
        valid_books = []
        for title, rating in books:
            if 1 <= rating <= 5:
                valid_books.append((title, rating))
        cleaned[user] = valid_books

    return cleaned
    """,
    'g1_task2_w2': """
def report(reading_list):
    total_readers = len(reading_list)

    total_ratings = 0
    rating_count = 0
    book_count = {}

    for books in reading_list.values():
        for title, rating in books:
            total_ratings += rating
            rating_count += 1

            if title in book_count:
                book_count[title] += 1
            else:
                book_count[title] = 1

    overall_average = round(total_ratings / rating_count, 2)

    most_popular_book = max(book_count, key=book_count.get)

    print(f"Number of people: {total_readers}")
    print(f"Overall average rating: {overall_average}")
    print(f"Most popular book: {most_popular_book}")

report(reading_list)
""",
    'g1_task3_w2': """
def average_rating(reading_list, book_name):
    total = 0
    count = 0

    reading_list = clean_reading_list(reading_list)
    for books in reading_list.values():
        for book, rating in books:
            if book == book_name:
                total += rating
                count += 1

    if count == 0:
        return 0
    return total / count

avgRatingHobbit = average_rating(reading_list, "Hobbit")
avgRating1984 = average_rating(reading_list, "1984")

print("Average rating Hobbit:", avgRatingHobbit)
print("Average rating 1984:", avgRating1984)
""",
    'g1_task4_w2': """
def print_book_overview(reading_list):
    book_totals = {}  
    book_counts = {}  

    reading_list = clean_reading_list(reading_list)


    for books in reading_list.values():
        for book, rating in books:
            if book in book_totals:
                book_totals[book] += rating
                book_counts[book] += 1
            else:
                book_totals[book] = rating
                book_counts[book] = 1


    for book in book_totals:
        avg = book_totals[book] / book_counts[book]
        count = book_counts[book]
        print(f"{book:<10} | Avg: {avg:.1f} | Ratings: {count}")
""",
    'g1_task5_w2': """
def rating_category(avg):
    if avg >= 4.5:
        return "Must Read"
    elif avg >= 3.5:
        return "Recommended"
    else:
        return "Skip"
""",
    'g1_task6_w2': """
def print_overview(reading_list):
    reading_list = clean_reading_list(reading_list)
    all_books = set()
    for books in reading_list.values():
        for book, _ in books:
            all_books.add(book)
        
    for book in all_books:
        avg = average_rating(reading_list, book)      
        category = rating_category(avg)
        
        count = 0
        for books in reading_list.values():
            for b, _ in books:
                if b == book:
                    count += 1

        print(f"{book:<10} | Avg: {avg:.2f} | Ratings: {count} | {category:<9} |")
""",
    'g2_task1_w2': """
def clean_evaluations(course_evals):
    cleaned = {}

    for student, course in course_evals.items():
        valid_course = []
        for name, rating in course:
            if 1 <= rating <= 5:
                valid_course.append((name, rating))
        cleaned[student] = valid_course

    return cleaned
""",
    'g2_task2_w2': """
def report(course_evals):
    total_students = len(course_evals)

    total_ratings = 0
    rating_count = 0
    course_count = {}

    for courses in course_evals.values():
        for name, rating in courses:
            total_ratings += rating
            rating_count += 1

            if name in course_count:
                course_count[name] += 1
            else:
                course_count[name] = 1

    overall_average = round(total_ratings / rating_count, 2)

    most_popular_course = max(course_count, key=course_count.get)

    print(f"Number of students: {total_students}")
    print(f"Overall average rating: {overall_average}")
    print(f"Most popular course: {most_popular_course}")

report(course_evals)
""",
    'g2_task3_w2': """
def average_rating(course_evals, course_name):
    total = 0
    count = 0

    course_evals = clean_evaluations(course_evals)
    for courses in course_evals.values():
        for course, rating in courses:
            if course == course_name:
                total += rating
                count += 1

    if count == 0:
        return 0
    return total / count

avgRatingCalculus = average_rating(course_evals, "Calculus")
avgRatingDataScience = average_rating(course_evals, "Data Science")

print("Average rating Calculus:", avgRatingCalculus)
print("Average rating Data Science:", avgRatingDataScience)
""",
    'g2_task4_w2': """
def print_course_overview(course_evals):
    course_totals = {}  
    course_counts = {}  

    course_evals = clean_evaluations(course_evals)


    for courses in course_evals.values():
        for course, rating in courses:
            if course in course_totals:
                course_totals[course] += rating
                course_counts[course] += 1
            else:
                course_totals[course] = rating
                course_counts[course] = 1


    for course in course_totals:
        avg = course_totals[course] / course_counts[course]
        count = course_counts[course]
        print(f"{course:<10} | Avg: {avg:.1f} | Ratings: {count}")
""",
    'g2_task5_w2': """
def rating_category(avg):
    if avg >= 4.5:
        return "Outstanding"
    elif avg >= 3.5:
        return "Good"
    else:
        return "Needs Improvement"
""",
    'g2_task6_w2': """
def print_overview(course_evals):
    course_evals = clean_evaluations(course_evals)
    all_courses = set()
    for courses in course_evals.values():
        for course, _ in courses:
            all_courses.add(course)
        
    for course in all_courses:
        avg = average_rating(course_evals, course)      
        category = rating_category(avg)
        
        count = 0
        for courses in course_evals.values():
            for m, _ in courses:
                if m == course:
                    count += 1

        print(f"{course:<10} | Avg: {avg:.2f} | Ratings: {count} | {category:<9} |")
""",
    'g3_task1_w2': """
def clean_reviews(cafe_reviews):
    cleaned = {}

    for customer, cafes in cafe_reviews.items():
        valid_cafes = []
        for name, rating in cafes:
            if 1 <= rating <= 5:
                valid_cafes.append((name, rating))
        cleaned[customer] = valid_cafes

    return cleaned
""",
    'g3_task2_w2': """
def report(cafe_reviews):
    total_customers = len(cafe_reviews)

    total_ratings = 0
    rating_count = 0
    cafe_count = {}

    for cafes in cafe_reviews.values():
        for title, rating in cafes:
            total_ratings += rating
            rating_count += 1

            if title in cafe_count:
                cafe_count[title] += 1
            else:
                cafe_count[title] = 1

    overall_average = round(total_ratings / rating_count, 2)

    most_popular_cafe = max(cafe_count, key=cafe_count.get)

    print(f"Number of customers: {total_customers}")
    print(f"Overall average rating: {overall_average}")
    print(f"Most popular movie: {most_popular_cafe}")

report(cafe_reviews)
""",
    'g3_task3_w2': """
def average_rating(cafe_reviews, cafe_name):
    total = 0
    count = 0

    cafe_reviews = clean_reviews(cafe_reviews)

    for cafes in cafe_reviews.values():
        for cafe, rating in cafes:
            if cafe == cafe_name:
                total += rating
                count += 1

    if count == 0:
        return 0
    return total / count

avgRatingCafeNoir = average_rating(cafe_reviews, "Cafe Noir")
avgRatingJavaHouse = average_rating(cafe_reviews, "Java House")

print("Average rating Cafe Noir:", avgRatingCafeNoir)
print("Average rating Java House:", avgRatingJavaHouse)
""",
    'g3_task4_w2': """
def print_cafe_overview(cafe_reviews):
    cafe_totals = {}  
    cafe_counts = {}  

    cafe_reviews = clean_reviews(cafe_reviews)


    for cafes in cafe_reviews.values():
        for cafe, rating in cafes:
            if cafe in cafe_totals:
                cafe_totals[cafe] += rating
                cafe_counts[cafe] += 1
            else:
                cafe_totals[cafe] = rating
                cafe_counts[cafe] = 1


    for cafe in cafe_totals:
        avg = cafe_totals[cafe] / cafe_counts[cafe]
        count = cafe_counts[cafe]
        print(f"{cafe:<10} | Avg: {avg:.1f} | Ratings: {count}")
""",
    'g3_task5_w2': """
def rating_category(avg):
    if avg >= 4.5:
        return "Outstanding"
    elif avg >= 3.5:
        return "Solid Choice"
    else:
        return "Avoid"
""",
    'g3_task6_w2': """
def print_overview(cafe_reviews):
    cafe_reviews = clean_reviews(cafe_reviews)
    all_cafes = set()
    for cafes in cafe_reviews.values():
        for cafe, _ in cafes:
            all_cafes.add(cafe)
        
    for cafe in all_cafes:
        avg = average_rating(cafe_reviews, cafe)      
        category = rating_category(avg)
        
        count = 0
        for cafes in cafe_reviews.values():
            for c, _ in cafes:
                if c == cafe:
                    count += 1

        print(f"{cafe:<10} | Avg: {avg:.2f} | Ratings: {count} | {category:<9} |")
""",
    'g4_task1_w2': """
def clean_reviews(course_reviews):
    cleaned = {}

    for member, courses in course_reviews.items():
        valid_courses = []
        for title, rating in courses:
            if 1 <= rating <= 5:
                valid_courses.append((title, rating))
        cleaned[member] = valid_courses

    return cleaned
""",
    'g4_task2_w2': """
def report(course_reviews):
    total_members = len(course_reviews)

    total_ratings = 0
    rating_count = 0
    course_count = {}

    for courses in course_reviews.values():
        for title, rating in courses:
            total_ratings += rating
            rating_count += 1

            if title in course_count:
                course_count[title] += 1
            else:
                course_count[title] = 1

    overall_average = round(total_ratings / rating_count, 2)

    most_popular_course = max(course_count, key=course_count.get)

    print(f"Number of members: {total_members}")
    print(f"Overall average rating: {overall_average}")
    print(f"Most popular course: {most_popular_course}")


report(course_reviews)
""",
    'g4_task3_w2': """
def average_rating(course_reviews, course_name):
    total = 0
    count = 0

    course_reviews = clean_reviews(course_reviews)
    # Alle Nutzer durchgehen
    for courses in course_reviews.values():
        for courses, rating in courses:
            if courses == course_name:
                total += rating
                count += 1

    if count == 0:
        return 0
    return total / count

avgRatingPilates = average_rating(course_reviews, "Pilates")
avgRatingYogaFlow = average_rating(course_reviews, "Yoga Flow")

print("Average rating Pilates:", avgRatingPilates)
print("Average rating Yoga Flow:", avgRatingYogaFlow)
""",
    'g4_task4_w2': """
def print_course_overview(course_reviews):
    course_totals = {}  
    course_counts = {}  

    course_reviews = clean_reviews(course_reviews)


    for courses in course_reviews.values():
        for course, rating in courses:
            if course in course_totals:
                course_totals[course] += rating
                course_counts[course] += 1
            else:
                course_totals[course] = rating
                course_counts[course] = 1


    for course in course_totals:
        avg = course_totals[course] / course_counts[course]
        count = course_counts[course]
        print(f"{course:<10} | Avg: {avg:.1f} | Ratings: {count}")
""",
    'g4_task5_w2': """
def rating_category(avg):
    if avg >= 4.5:
        return "Top Rated"
    elif avg >= 3.5:
        return "Popular"
    else:
        return "Unpopular"
""",
    'g4_task6_w2': """
def print_overview(course_reviews):
    course_reviews = clean_reviews(course_reviews)
    all_courses = set()
    for courses in course_reviews.values():
        for course, _ in courses:
            all_courses.add(course)
        
    for course in all_courses:
        avg = average_rating(course_reviews, course)      
        category = rating_category(avg)
        
        count = 0
        for courses in course_reviews.values():
            for c, _ in courses:
                if c == course:
                    count += 1

        print(f"{course:<10} | Avg: {avg:.2f} | Ratings: {count} | {category:<9} |")
""",
    'g5_task1_w2': """
def clean_ratings(album_ratings):
    cleaned = {}

    for listener, albums in album_ratings.items():
        valid_albums = []
        for title, rating in albums:
            if 1 <= rating <= 5:
                valid_albums.append((title, rating))
        cleaned[listener] = valid_albums

    return cleaned
""",
    'g5_task2_w2': """
def report(album_ratings):
    total_listeners = len(album_ratings)

    total_ratings = 0
    rating_count = 0
    album_count = {}

    for albums in album_ratings.values():
        for title, rating in albums:
            total_ratings += rating
            rating_count += 1

            if title in album_count:
                album_count[title] += 1
            else:
                album_count[title] = 1

    overall_average = round(total_ratings / rating_count, 2)

    most_popular_album = max(album_count, key=album_count.get)

    print(f"Number of listeners: {total_listeners}")
    print(f"Overall average rating: {overall_average}")
    print(f"Most popular album: {most_popular_album}")


report(album_ratings)
""",
    'g5_task3_w2': """
def average_rating(album_ratings, album_name):
    total = 0
    count = 0

    album_ratings = clean_ratings(album_ratings)
    # Alle Nutzer durchgehen
    for albums in album_ratings.values():
        for album, rating in albums:
            if album == album_name:
                total += rating
                count += 1

    if count == 0:
        return 0
    return total / count

avgRatingRumours = average_rating(album_ratings, "Rumours")
avgRatingAbbeyRoad = average_rating(album_ratings, "Abbey Road")

print("Average rating Rumours:", avgRatingRumours)
print("Average rating Abbey Road:", avgRatingAbbeyRoad)
""",
    'g5_task4_w2': """
def print_album_overview(album_ratings):
    album_totals = {}  
    album_counts = {}  

    album_ratings = clean_ratings(album_ratings)


    for albums in album_ratings.values():
        for album, rating in albums:
            if album in album_totals:
                album_totals[album] += rating
                album_counts[album] += 1
            else:
                album_totals[album] = rating
                album_counts[album] = 1


    for album in album_totals:
        avg = album_totals[album] / album_counts[album]
        count = album_counts[album]
        print(f"{album:<10} | Avg: {avg:.1f} | Ratings: {count}")
""",
    'g5_task5_w2': """
def rating_category(avg):
    if avg >= 4.5:
        return "Classic"
    elif avg >= 3.5:
        return "Great"
    else:
        return "Mediocre"
""",
    'g5_task6_w2': """
def print_overview(album_ratings):
    album_ratings = clean_ratings(album_ratings)
    all_albums = set()
    for albums in album_ratings.values():
        for album, _ in albums:
            all_albums.add(album)
        
    for album in all_albums:
        avg = average_rating(album_ratings, album)      
        category = rating_category(avg)
        
        count = 0
        for albums in album_ratings.values():
            for a, _ in albums:
                if a == album:
                    count += 1

        print(f"{album:<10} | Avg: {avg:.2f} | Ratings: {count} | {category:<9} |")
""",
    'g6_task1_w2': """
def clean_ratings(podcast_ratings):
    cleaned = {}

    for listener in podcast_ratings:
        podcasts = podcast_ratings[listener]
        valid_podcasts = []

        for podcast in podcasts:
            name = podcast[0]
            rating = podcast[1]

            # Nur Bewertungen zwischen 1 und 5 behalten
            if 1 <= rating <= 5:
                valid_podcasts.append((name, rating))

        cleaned[listener] = valid_podcasts

    return cleaned
""",
    'g6_task2_w2': """
def report(podcast_ratings):
    total_listeners = len(podcast_ratings)

    total_ratings = 0
    num_ratings = 0
    podcast_count = {}

    for listener_reviews in podcast_ratings.values():
        for podcast, rating in listener_reviews:
            total_ratings += rating
            num_ratings += 1

            if podcast in podcast_count:
                podcast_count[podcast] += 1
            else:
                podcast_count[podcast] = 1

    overall_average = round(total_ratings / num_ratings, 2)

    most_popular_podcast = max(podcast_count, key=podcast_count.get)

    print(f"Number of listeners: {total_listeners}")
    print(f"Overall average rating: {overall_average}")
    print(f"Most popular podcast: {most_popular_podcast}")

report(podcast_ratings)
""",
    'g6_task3_w2': """
def average_rating(podcast_ratings, podcast_name):
    total = 0
    count = 0

    for listener_reviews in podcast_ratings.values():
        for podcast, rating in listener_reviews:
            if podcast == podcast_name:
                total += rating
                count += 1

    if count == 0:
        return 0

    return total / count

avgRatingHistoryHour = average_rating(podcast_ratings, "History Hour")
avgRatingTechTalk = average_rating(podcast_ratings, "Tech Talk")

print(f"Average rating History Hour: {avgRatingHistoryHour:.1f}")
print(f"Average rating Tech Talk: {avgRatingTechTalk:.1f}")
""",
    'g6_task4_w2': """
def print_podcast_overview(podcast_ratings):
    podcast_totals = {} 
    podcast_counts = {}  

    podcast_ratings = clean_ratings(podcast_ratings)

    for listener_reviews in podcast_ratings.values():
        for podcast, rating in listener_reviews:
            if podcast in podcast_totals:
                podcast_totals[podcast] += rating
                podcast_counts[podcast] += 1
            else:
                podcast_totals[podcast] = rating
                podcast_counts[podcast] = 1

    for podcast in podcast_totals:
        avg = podcast_totals[podcast] / podcast_counts[podcast]
        count = podcast_counts[podcast]
        print(f"{podcast:<12} | Avg: {avg:.1f} | Ratings: {count}")

print_podcast_overview(podcast_ratings)
""",
    'g6_task5_w2': """
def rating_category(avg):
    if avg >= 4.5:
        return "Must Listen"
    elif avg >= 3.5:
        return "Worth It"
    else:
        return "Skip"
""",
    'g6_task6_w2': """
def print_overview(podcast_ratings):
    podcast_totals = {}
    podcast_counts = {}

    podcast_ratings = clean_ratings(podcast_ratings)

    for listener_reviews in podcast_ratings.values():
        for podcast, rating in listener_reviews:
            if podcast in podcast_totals:
                podcast_totals[podcast] += rating
                podcast_counts[podcast] += 1
            else:
                podcast_totals[podcast] = rating
                podcast_counts[podcast] = 1

    for podcast in podcast_totals:
        avg = podcast_totals[podcast] / podcast_counts[podcast]
        count = podcast_counts[podcast]
        category = rating_category(avg)
        print(f"{podcast:<12} | Avg: {avg:.2f} | Ratings: {count} | {category:<11} |")

print_overview(podcast_ratings)
""",
    'g7_task1_w2': """
def clean_reviews(reviews):
    cleaned = {}

    for person in reviews:
        restaurant_reviews = reviews[person]
        valid_reviews = []

        for review in restaurant_reviews:
            restaurant = review[0]
            rating = review[1]

            if 1 <= rating <= 5:
                valid_reviews.append((restaurant, rating))

        cleaned[person] = valid_reviews

    return cleaned
""",
    'g7_task2_w2': """
def report(reviews):
    total_reviewers = len(reviews)

    total_ratings = 0
    num_ratings = 0
    restaurant_count = {}

    for reviewer_reviews in reviews.values():
        for restaurant, rating in reviewer_reviews:
            total_ratings += rating
            num_ratings += 1

            if restaurant in restaurant_count:
                restaurant_count[restaurant] += 1
            else:
                restaurant_count[restaurant] = 1

    overall_average = round(total_ratings / num_ratings, 2)

    most_popular_restaurant = max(restaurant_count, key=restaurant_count.get)

    print(f"Number of reviewers: {total_reviewers}")
    print(f"Overall average rating: {overall_average}")
    print(f"Most popular restaurant: {most_popular_restaurant}")


report(reviews)
""",
    'g7_task3_w2': """
def average_rating(reviews, restaurant_name):
    total = 0
    count = 0

    for reviewer_reviews in reviews.values():
        for restaurant, rating in reviewer_reviews:
            if restaurant == restaurant_name:
                total += rating
                count += 1

    if count == 0:
        return 0  # kein Rating vorhanden

    return total / count

avgRatingBurgerKing = average_rating(reviews, "Burger King")
avgRatingPizzaPalace = average_rating(reviews, "Pizza Palace")

print(f"Average rating Burger King: {avgRatingBurgerKing:.1f}")
print(f"Average rating Pizza Palace: {avgRatingPizzaPalace:.1f}")
""",
    'g7_task4_w2': """
def print_restaurant_overview(reviews):
    restaurant_totals = {}  
    restaurant_counts = {} 

    reviews = clean_reviews(reviews)

    for reviewer_reviews in reviews.values():
        for restaurant, rating in reviewer_reviews:
            if restaurant in restaurant_totals:
                restaurant_totals[restaurant] += rating
                restaurant_counts[restaurant] += 1
            else:
                restaurant_totals[restaurant] = rating
                restaurant_counts[restaurant] = 1

    for restaurant in restaurant_totals:
        avg = restaurant_totals[restaurant] / restaurant_counts[restaurant]
        count = restaurant_counts[restaurant]
        print(f"{restaurant:<12} | Avg: {avg:.1f} | Ratings: {count}")
        

print_restaurant_overview(reviews)
""",
    'g7_task5_w2': """
def rating_category(avg):
    if avg >= 4.5:
        return "Outstanding"
    elif avg >= 3.5:
        return "Solid Choice"
    else:
        return "Avoid"
""",
    'g7_task6_w2': """
def print_overview(reviews):
    restaurant_totals = {}
    restaurant_counts = {}

    reviews = clean_reviews(reviews)

    for reviewer_reviews in reviews.values():
        for restaurant, rating in reviewer_reviews:
            if restaurant in restaurant_totals:
                restaurant_totals[restaurant] += rating
                restaurant_counts[restaurant] += 1
            else:
                restaurant_totals[restaurant] = rating
                restaurant_counts[restaurant] = 1

    for restaurant in restaurant_totals:
        avg = restaurant_totals[restaurant] / restaurant_counts[restaurant]
        count = restaurant_counts[restaurant]
        category = rating_category(avg)
        print(f"{restaurant:<12} | Avg: {avg:.2f} | Ratings: {count} | {category} |")

print_overview(reviews)
""",
    'g8_task1_w2': """
def clean_reviews(destination_reviews):
    cleaned = {}

    for traveler in destination_reviews:
        reviews = destination_reviews[traveler]
        valid_reviews = []

        for review in reviews:
            destination = review[0]
            rating = review[1]

            if 1 <= rating <= 5:
                valid_reviews.append((destination, rating))

        cleaned[traveler] = valid_reviews

    return cleaned


#Testcase
print(clean_reviews(destination_reviews))
""",
    'g8_task2_w2': """
def report(destination_reviews):
    total_travelers = len(destination_reviews)

    total_ratings = 0
    num_ratings = 0
    destination_count = {}

    for reviews in destination_reviews.values():
        for destination, rating in reviews:
            total_ratings += rating
            num_ratings += 1

            if destination in destination_count:
                destination_count[destination] += 1
            else:
                destination_count[destination] = 1

    overall_average = round(total_ratings / num_ratings, 2)

    most_popular_destination = max(destination_count, key=destination_count.get)

    # Ausgabe
    print(f"Number of travelers: {total_travelers}")
    print(f"Overall average rating: {overall_average}")
    print(f"Most popular destination: {most_popular_destination}")


report(destination_reviews)
""",
    'g8_task3_w2': """
def average_rating(destination_reviews, destination_name):
    total = 0
    count = 0

    for reviews in destination_reviews.values():
        for destination, rating in reviews:
            if destination == destination_name:
                total += rating
                count += 1

    if count == 0:
        return 0

    return total / count


avgRatingLondon = average_rating(destination_reviews, "London")
avgRatingParis = average_rating(destination_reviews, "Paris")

print(f"Average rating London: {avgRatingLondon:.1f}")
print(f"Average rating Paris: {avgRatingParis:.1f}")
""",
    'g8_task4_w2': """
def print_destination_overview(destination_reviews):
    destination_totals = {}  
    destination_counts = {}  

    destination_reviews = clean_reviews(destination_reviews)

    for reviews in destination_reviews.values():
        for destination, rating in reviews:
            if destination in destination_totals:
                destination_totals[destination] += rating
                destination_counts[destination] += 1
            else:
                destination_totals[destination] = rating
                destination_counts[destination] = 1

    for destination in destination_totals:
        avg = destination_totals[destination] / destination_counts[destination]
        count = destination_counts[destination]
        print(f"{destination:<12} | Avg: {avg:.1f} | Ratings: {count}")

print_destination_overview(destination_reviews)
""",
    'g8_task5_w2': """
def rating_category(avg):
    if avg >= 4.5:
        return "Must Visit"
    elif avg >= 3.5:
        return "Recommended"
    else:
        return "Not Recommended"
""",
    'g8_task6_w2': """
def print_overview(destination_reviews):
    destination_totals = {}
    destination_counts = {}

    destination_reviews = clean_reviews(destination_reviews)

    for reviews in destination_reviews.values():
        for destination, rating in reviews:
            if destination in destination_totals:
                destination_totals[destination] += rating
                destination_counts[destination] += 1
            else:
                destination_totals[destination] = rating
                destination_counts[destination] = 1

    for destination in destination_totals:
        avg = destination_totals[destination] / destination_counts[destination]
        count = destination_counts[destination]
        category = rating_category(avg)
        print(f"{destination:<12} | Avg: {avg:.2f} | Ratings: {count} | {category} |")

print_overview(destination_reviews)
""",
    'g9_task1_w2': """
def clean_scores(game_scores):
    cleaned = {}

    for player in game_scores:
        games = game_scores[player]
        valid_games = []

        for game in games:
            title = game[0]
            rating = game[1]

            if 1 <= rating <= 5:
                valid_games.append((title, rating))

        cleaned[player] = valid_games

    return cleaned


#Testcase
print(clean_scores(game_scores))
""",
    'g9_task2_w2': """
def report(game_scores):
    total_players = len(game_scores)

    total_ratings = 0
    num_ratings = 0
    game_count = {}

    for games in game_scores.values():
        for title, rating in games:
            total_ratings += rating
            num_ratings += 1

            if title in game_count:
                game_count[title] += 1
            else:
                game_count[title] = 1

    overall_average = total_ratings / num_ratings
    most_popular_game = max(game_count, key=game_count.get)

    print(f"Number of players: {total_players}")
    print(f"Overall average rating: {overall_average}")
    print(f"Most popular game: {most_popular_game}")

report(game_scores)
""",
    'g9_task3_w2': """
def average_score(game_scores, game_name):
    total = 0
    count = 0

    for games in game_scores.values():
        for title, rating in games:
            if title == game_name:
                total += rating
                count += 1

    if count == 0:
        return 0  # kein Rating vorhanden

    return total / count


avgRatingSonic = average_score(game_scores, "Sonic")
avgRatingZelda = average_score(game_scores, "Zelda")

print(f"Average rating Sonic: {avgRatingSonic:.1f}")
print(f"Average rating Zelda: {avgRatingZelda:.1f}")
""",
    'g9_task4_w2': """
def print_game_overview(game_scores):
    game_totals = {}  
    game_counts = {}  
    game_scores = clean_scores(game_scores)

    for games in game_scores.values():
        for game, rating in games:
            if game in game_totals:
                game_totals[game] += rating
                game_counts[game] += 1
            else:
                game_totals[game] = rating
                game_counts[game] = 1

    for game in game_totals:
        avg = game_totals[game] / game_counts[game]
        count = game_counts[game]
        print(f"{game:<12} | Avg: {avg:.1f} | Ratings: {count}")
""",
    'g9_task5_w2': """
def rating_category(avg):
    if avg >= 4.5:
        return "Masterpiece"
    elif avg >= 3.5:
        return "Worth Playing"
    else:
        return "Pass"
        
#Testcase
avg = 0
print(rating_category(avg))
""",
    'g9_task6_w2': """
def print_overview(game_scores):
    game_totals = {}
    game_counts = {}

    game_scores = clean_scores(game_scores)

    for games in game_scores.values():
        for game, rating in games:
            if game in game_totals:
                game_totals[game] += rating
                game_counts[game] += 1
            else:
                game_totals[game] = rating
                game_counts[game] = 1

    for game in sorted(game_totals):
        avg = game_totals[game] / game_counts[game]
        count = game_counts[game]
        category = rating_category(avg)
        print(f"{game:<12} | Avg: {avg:.2f} | Ratings: {count} | {category} |")

print_overview(game_scores)
""",
    'g1_task1_w3': """
def extract_ids(raw_ids):
    cleaned_codes = []

    for student_id in raw_ids:
        invalid = False  
        cleaned = ""

        for c in student_id:
            if c == "#" or c == "$":
                invalid = True
                break

            if c == " " or c == "-" or c == ".":
                continue

            cleaned += c

        if not invalid:
            cleaned_codes.append(cleaned.upper())

    return cleaned_codes
""",
    'g1_task2_w3': """
def create_verification_digit(student_id):
    first_8 = student_id[:8]
    
    total = 0
    
    for char in first_8:
        if char.isdigit():
            total += int(char)
    
    verification_digit = total % 10
    
    return verification_digi
""",
    'g1_task3_w3': """
def correct_verification_digits(raw_ids):
    cleaned_ids = extract_ids(raw_ids)
    corrected_ids = []
    
    for code in cleaned_ids:
        expected_digit = str(create_verification_digit(code))
        
        corrected = False
        if code[-1] != expected_digit:
            code = code[:-1] + expected_digit
            corrected = True
        
        corrected_ids.append(code)
        
        if corrected:
            print(f"{code} → Verification digit corrected")
        else:
            print(f"{code} → Verification digit already correct")
    
    return corrected_ids
""",
    'g1_task4_w3': """
def verification_report(raw_ids):
    cleaned_ids = extract_ids(raw_ids)

    correct = 0
    incorrect = 0

    for code in cleaned_ids:
        expected_verification = str(create_verification_digit(code))
        actual_verification = code[-1]

        if actual_verification == expected_verification:
            correct += 1
        else:
            incorrect += 1

    total = correct + incorrect
    percentage_incorrect = (incorrect / total) * 100 if total > 0 else 0

    print(f"Number of correct codes: {correct}")
    print(f"Number of incorrect codes: {incorrect}")
    print(f"Percentage of incorrect codes: {percentage_incorrect}%")

verification_report(raw_ids)
""",
    'g1_task5_w3': """
def format_id(student_id):
    part1 = student_id[:2]       
    part2 = student_id[2:6]      
    part3 = student_id[6:]       
    
    formatted = f"{part1}-{part2}-{part3}"
    return formatted
""",
    'g1_task6_w3': """
def add_department(raw_ids):
    cleaned_ids = extract_ids(raw_ids)
    categorized_ids = []

    for student_id in cleaned_ids:
        prefix = student_id[:2]

        if prefix in ["ST", "EN"]:
            department = "Engineering"
        elif prefix == "CS":
            department = "Computer Science"
        elif prefix in ["MA", "PH"]:
            department = "Natural Sciences"
        else:
            department = "Unknown"

        categorized_ids.append((student_id, department))

    return categorized_ids
""",
    'g2_task1_w3': """
def extract_skus(raw_skus):
    cleaned_skus = []

    for sku in raw_skus:
        invalid = False   
        cleaned = ""

        for c in sku:
            if c == "&" or c == "@":
                invalid = True
                break

            if c == " " or c == "." or c == "-":
                continue

            cleaned += c

        if not invalid:
            cleaned_skus.append(cleaned.upper())

    return cleaned_skus
""",
    'g2_task2_w3': """
def calculate_check_digit(sku_code):
    first_9 = sku_code[:9]
    
    total = 0
    
    for char in first_9:
        if char.isdigit():        
            total += int(char)  
    
    check_digit = total % 10
    
    return check_digit
""",
    'g2_task3_w3': """
def correct_check_digits(raw_skus):
    cleaned_skus = extract_skus(raw_skus)
    corrected_skus = []
    
    for code in cleaned_skus:
        expected_check = str(calculate_check_digit(code))  
        
        corrected = False
        if code[-1] != expected_check:
            code = code[:-1] + expected_check
            corrected = True
        
        corrected_skus.append(code)
        
        if corrected:
            print(f"{code} → Check digit corrected")
        else:
            print(f"{code} → Check digit already correct")
    
    return corrected_skus
""",
    'g2_task4_w3': """
def sku_report(raw_skus):
    cleaned_skus = extract_skus(raw_skus)

    correct = 0
    incorrect = 0

    for code in cleaned_skus:
        expected_check = str(calculate_check_digit(code))
        actual_check = code[-1]

        if actual_check == expected_check:
            correct += 1
        else:
            incorrect += 1

    total = correct + incorrect
    percentage_incorrect = (incorrect / total) * 100 if total > 0 else 0

    print(f"Number of correct codes: {correct}")
    print(f"Number of incorrect codes: {incorrect}")
    print(f"Percentage of incorrect codes: {percentage_incorrect}%")

sku_report(raw_skus)
""",
    'g2_task5_w3': """
def format_sku(sku):
    part1 = sku[:2]       
    part2 = sku[2:6]     
    part3 = sku[6:-1]     
    check_char = sku[-1] 

    formatted = f"{part1}-{part2}-{part3}{check_char}"
    return formatted
""",
    'g2_task6_w3': """
def add_category(raw_skus):
    cleaned_skus = extract_skus(raw_skus)
    categorized_skus = []

    for sku in cleaned_skus:
        prefix = sku[:2]

        if prefix in ["EL", "SP"]:
            category = "Electronics"
        elif prefix == "FD":
            category = "Food & Beverage"
        elif prefix in ["CL", "TO"]:
            category = "Clothing"
        else:
            category = "Unknown"

        categorized_skus.append((sku, category))

    return categorized_skus
    
add_category(raw_skus)
""",
    'g3_task1_w3': """
def extract_card_numbers(raw_cards):
    cleaned_cards = []

    for card in raw_cards:
        invalid = False  
        cleaned = ""

        for c in card:
            if c == "#" or c == "*":
                invalid = True
                break

            if c == " " or c == "." or c == "-":
                continue

            cleaned += c

        if not invalid:
            cleaned_cards.append(cleaned.upper())

    return cleaned_cards
""",
    'g3_task2_w3': """
def calculate_luhn(card_number):
    first_15 = card_number[:15]
    
    total = 0
    
    for char in first_15:
        if char.isdigit():    
            total += int(char) 
    
    luhn_digit = total % 10
    
    return luhn_digit
""",
    'g3_task3_w3': """
def correct_luhn_digits(raw_cards):
    cleaned_cards = extract_card_numbers(raw_cards)
    corrected_cards = []
    
    for code in cleaned_cards:
        expected_luhn = str(calculate_luhn(code))
        
        corrected = False
        if code[-1] != expected_luhn:
            code = code[:-1] + expected_luhn
            corrected = True
        
        corrected_cards.append(code)
        
        if corrected:
            print(f"{code} → Luhn check digit corrected")
        else:
            print(f"{code} → Luhn check digit already correct")
    
    return corrected_cards
""",
    'g3_task4_w3': """
def card_report(raw_cards):
    cleaned_cards = extract_card_numbers(raw_cards)

    correct = 0
    incorrect = 0

    for code in cleaned_cards:
        expected_luhn = str(calculate_luhn(code))
        actual_luhn = code[-1]

        if actual_luhn == expected_luhn:
            correct += 1
        else:
            incorrect += 1

    total = correct + incorrect
    percentage_incorrect = (incorrect / total) * 100 if total > 0 else 0

    print(f"Number of correct codes: {correct}")
    print(f"Number of incorrect codes: {incorrect}")
    print(f"Percentage of incorrect codes: {percentage_incorrect}%")

card_report(raw_cards)
""",
    'g3_task5_w3': """
def format_card(card_number):
    part1 = card_number[:4]       
    part2 = card_number[4:8]      
    part3 = card_number[8:12]    
    part4 = card_number[12:-1]    
    check_char = card_number[-1] 

    formatted = f"{part1}-{part2}-{part3}-{part4}{check_char}"
    return formatted
""",
    'g3_task6_w3': """
def add_card_type(raw_cards):
    cleaned_cards = extract_card_numbers(raw_cards)
    categorized_cards = []

    for card in cleaned_cards:
        prefix = card[0]

        if prefix == "4":
            card_type = "Visa"
        elif prefix == "5":
            card_type = "Mastercard"
        elif prefix == "3":
            card_type = "American Express"
        elif prefix == "6":
            card_type = "Discover"
        else:
            card_type = "Unknown"

        categorized_cards.append((card, card_type))

    return categorized_cards

add_card_type(raw_cards)
""",
    'g4_task1_w3': """
def extract_plates(raw_plates):
    cleaned_ids = []

    for plate in raw_plates:
        invalid = False   
        cleaned = ""

        for c in plate:
            if c == "^" or c == "%":
                invalid = True
                break

            if c == " " or c == "." or c == "-":
                continue

            cleaned += c

        if not invalid:
            cleaned_ids.append(cleaned.upper())

    return cleaned_ids
""",
    'g4_task2_w3': """
def calculate_control_char(plate):
    first_6 = plate[:6]
    
    total = 0
    
    for char in first_6:
        if char.isdigit():        
            total += int(char)    
            
    control_char = total % 10
    
    return control_char
""",
    'g4_task3_w3': """
def correct_control_chars(raw_plates):
    cleaned_plates = extract_plates(raw_plates)
    corrected_plates = []
    
    for code in cleaned_plates:
        expected_control = str(calculate_control_char(code))
        
        corrected = False
        if code[-1] != expected_control:
            code = code[:-1] + expected_control
            corrected = True
        
        corrected_plates.append(code)
        
        if corrected:
            print(f"{code} → Control character corrected")
        else:
            print(f"{code} → Control character already correct")
    
    return corrected_plates
""",
    'g4_task4_w3': """
def plate_report(raw_plates):
    cleaned_plates = extract_plates(raw_plates)

    correct = 0
    incorrect = 0

    for code in cleaned_plates:
        expected_control = str(calculate_control_char(code))
        actual_control = code[-1]

        if actual_control == expected_control:
            correct += 1
        else:
            incorrect += 1

    total = correct + incorrect
    percentage_incorrect = (incorrect / total) * 100 if total > 0 else 0

    print(f"Number of correct codes: {correct}")
    print(f"Number of incorrect codes: {incorrect}")
    print(f"Percentage of incorrect codes: {percentage_incorrect}%")

plate_report(raw_plates)
""",
    'g4_task5_w3': """
def format_plate(plate):
    # Write your code here
    #return
    part1 = plate[:2]       
    part2 = plate[2:5]      
    part3 = plate[5:-1]     
    check_char = plate[-1]  

    formatted = f"{part1}-{part2}-{part3}{check_char}"
    return formatted
""",
    'g4_task6_w3': """
def add_vehicle_type(raw_plates):
    cleaned_plates = extract_plates(raw_plates)
    categorized_plates = []

    for plate in cleaned_plates:
        prefix = plate[:1] 

        if prefix in ["A", "M"]:
            vehicle_type = "Private"
        elif prefix in ["X", "P"]:
            vehicle_type = "Business"
        elif prefix in ["R", "T"]:
            vehicle_type = "Government"
        else:
            vehicle_type = "Unknown"

        categorized_plates.append((plate, vehicle_type))

    return categorized_plates

add_vehicle_type(raw_plates)
""",
    'g5_task1_w3': """
def extract_bookings(raw_bookings):
    cleaned_bookings = []

    for booking in raw_bookings:
        invalid = False 
        cleaned = ""

        for c in booking:
            if c == "?" or c == "!":
                invalid = True
                break

            if c == " " or c == "." or c == "-":
                continue

            cleaned += c

        if not invalid:
            cleaned_bookings.append(cleaned.upper())

    return cleaned_bookings
""",
    'g5_task2_w3': """
def calculate_parity(booking_code):
    first_5 = booking_code[:5]
    
    total = 0
    
    for char in first_5:
        if char.isdigit():      
            total += int(char)  
    
    parity_digit = total % 10
    
    return parity_digit
""",
    'g5_task3_w3': """
def correct_parity_digits(raw_bookings):
    cleaned_bookings = extract_bookings(raw_bookings)
    corrected_bookings = []
    
    for code in cleaned_bookings:
        expected_parity = str(calculate_parity(code))
        
        corrected = False
        if code[-1] != expected_parity:
            code = code[:-1] + expected_parity
            corrected = True
        
        corrected_bookings.append(code)
        
        if corrected:
            print(f"{code} → Parity digit corrected")
        else:
            print(f"{code} → Parity digit already correct")
    
    return corrected_bookings
""",
    'g5_task4_w3': """
def booking_report(raw_bookings):
    cleaned_bookings = extract_bookings(raw_bookings)

    correct = 0
    incorrect = 0

    for code in cleaned_bookings:
        expected_parity = str(calculate_parity(code))
        actual_parity = code[-1]

        if actual_parity == expected_parity:
            correct += 1
        else:
            incorrect += 1

    total = correct + incorrect
    percentage_incorrect = (incorrect / total) * 100 if total > 0 else 0

    print(f"Number of correct codes: {correct}")
    print(f"Number of incorrect codes: {incorrect}")
    print(f"Percentage of incorrect codes: {percentage_incorrect}%")

booking_report(raw_bookings)
""",
    'g5_task5_w3': """
def format_booking(booking_code):
    part1 = booking_code[:2]       
    part2 = booking_code[2:-1]     
    check_char = booking_code[-1]  

    formatted = f"{part1}-{part2}-{check_char}"
    return formatted
""",
    'g5_task6_w3': """
def add_flight_class(raw_bookings):
    cleaned_bookings = extract_bookings(raw_bookings)
    categorized_bookings = []

    for code in cleaned_bookings:
        prefix = code[0]  

        if prefix in ["A", "M"]:
            flight_class = "Economy"
        elif prefix in ["X", "P"]:
            flight_class = "Business"
        elif prefix in ["R", "T"]:
            flight_class = "First Class"
        else:
            flight_class = "Unknown"

        categorized_bookings.append((code, flight_class))

    return categorized_bookings

add_flight_class(raw_bookings)
""",
    'g6_task1_w3': """
def extract_tracking(raw_tracking):
    cleaned_tracking = []

    for code in raw_tracking:
        invalid = False  
        cleaned = ""

        for c in code:
            if c == "@" or c == "&":
                invalid = True
                break

            if c == " " or c == "." or c == "-":
                continue

            cleaned += c

        if not invalid:
            cleaned_tracking.append(cleaned.upper())

    return cleaned_tracking
""",
    'g6_task2_w3': """
def calculate_checksum(tracking_number):
    first_11 = tracking_number[:11]
    
    total = 0
    
    for char in first_11:
        if char.isdigit():      
            total += int(char)   
    
   
    checksum_digit = total % 10
    
    return checksum_digit
""",
    'g6_task3_w3': """
def correct_checksums(raw_tracking):
    cleaned_tracking = extract_tracking(raw_tracking)
    corrected_tracking = []
    
    for code in cleaned_tracking:
        expected_checksum = str(calculate_checksum(code))
        
        corrected = False
        if code[-1] != expected_checksum:
            code = code[:-1] + expected_checksum
            corrected = True
        
        corrected_tracking.append(code)
        
        if corrected:
            print(f"{code} → Checksum digit corrected")
        else:
            print(f"{code} → Checksum digit already correct")
    
    return corrected_tracking
""",
    'g6_task4_w3': """
def tracking_report(raw_tracking):
    cleaned_tracking = extract_tracking(raw_tracking)

    correct = 0
    incorrect = 0

    for code in cleaned_tracking:
        expected_checksum = str(calculate_checksum(code))
        actual_checksum = code[-1]

        if actual_checksum == expected_checksum:
            correct += 1
        else:
            incorrect += 1

    total = correct + incorrect
    percentage_incorrect = (incorrect / total) * 100 if total > 0 else 0

    print(f"Number of correct codes: {correct}")
    print(f"Number of incorrect codes: {incorrect}")
    print(f"Percentage of incorrect codes: {percentage_incorrect}%")

tracking_report(raw_tracking)
""",
    'g6_task5_w3': """
def format_tracking(tracking_number):
    part1 = tracking_number[:2]       
    part2 = tracking_number[2:6]      
    part3 = tracking_number[6:10]     
    part4 = tracking_number[10:-1]    
    check_char = tracking_number[-1] 

    formatted = f"{part1}-{part2}-{part3}-{part4}{check_char}"
    return formatted
""",
    'g6_task6_w3': """
def add_region(raw_tracking):
    cleaned_tracking = extract_tracking(raw_tracking)
    categorized_tracking = []

    for code in cleaned_tracking:
        prefix = code[:2]

        if prefix in ["DE", "FR", "IT"]:
            region = "Europe"
        elif prefix == "US":
            region = "America"
        else:
            region = "Unknown"

        categorized_tracking.append((code, region))

    return categorized_tracking

add_region(raw_tracking)
""",
    'g7_task1_w3': """
def extract_badges(raw_badges):
    cleaned_badges = []

    for badge in raw_badges:
        invalid = False  
        cleaned = ""

        for c in badge:
            if c == "#" or c == "*":
                invalid = True
                break

            if c == " " or c == "." or c == "-":
                continue

            cleaned += c

        if not invalid:
            cleaned_badges.append(cleaned.upper())

    return cleaned_badges
""",
    'g7_task2_w3': """
def calculate_security_digit(badge_id):
    first_9 = badge_id[:9]
    
    total = 0
    
    for char in first_9:
        if char.isdigit():      
            total += int(char)   
    
    security_digit = total % 10
    
    return security_digit
""",
    'g7_task3_w3': """
def correct_security_digits(raw_badges):
    cleaned_badges = extract_badges(raw_badges)
    corrected_badges = []
    
    for code in cleaned_badges:
        expected_security = str(calculate_security_digit(code))
        
        corrected = False
        if code[-1] != expected_security:
            code = code[:-1] + expected_security
            corrected = True
        
        corrected_badges.append(code)
        
        if corrected:
            print(f"{code} → Security digit corrected")
        else:
            print(f"{code} → Security digit already correct")
    
    return corrected_badges
""",
    'g7_task4_w3': """
def badge_report(raw_badges):
    cleaned_badges = extract_badges(raw_badges)

    correct = 0
    incorrect = 0

    for code in cleaned_badges:
        expected_security = str(calculate_security_digit(code))
        actual_security = code[-1]

        if actual_security == expected_security:
            correct += 1
        else:
            incorrect += 1

    total = correct + incorrect
    percentage_incorrect = (incorrect / total) * 100 if total > 0 else 0

    print(f"Number of correct codes: {correct}")
    print(f"Number of incorrect codes: {incorrect}")
    print(f"Percentage of incorrect codes: {percentage_incorrect}%")
""",
    'g7_task5_w3': """
def format_badge(badge_id):
    part1 = badge_id[:2]       
    part2 = badge_id[2:6]     
    part3 = badge_id[6:-1]     
    check_char = badge_id[-1]

    formatted = f"{part1}-{part2}-{part3}{check_char}"
    return formatted
""",
    'g7_task6_w3': """
def add_department(raw_badges):
    cleaned_badges = extract_badges(raw_badges)
    categorized_badges = []

    for badge in cleaned_badges:
        prefix = badge[:2]

        if prefix == "HR":
            department = "Human Resources"
        elif prefix == "IT":
            department = "Information Technology"
        elif prefix in ["SL", "OP"]:
            department = "Operations"
        else:
            department = "Unknown"

        categorized_badges.append((badge, department))

    return categorized_badges

add_department(raw_badges)
""",
    'g8_task1_w3': """
def extract_prescriptions(raw_prescriptions):
    cleaned_prescriptions = []

    for code in raw_prescriptions:
        invalid = False  
        cleaned = ""

        for c in code:
            if c == "%" or c == "$":
                invalid = True
                break

            if c == " " or c == "." or c == "-":
                continue

            cleaned += c

        if not invalid:
            cleaned_prescriptions.append(cleaned.upper())

    return cleaned_prescriptions
""",
    'g8_task2_w3': """
def calculate_validation_digit(prescription_code):
    first_8 = prescription_code[:8]
    
    total = 0
    
    for char in first_8:
        if char.isdigit():       
            total += int(char)   
    
    validation_digit = total % 10
    
    return validation_digit
""",
    'g8_task3_w3': """
def correct_validation_digits(raw_prescriptions):
    cleaned_prescriptions = extract_prescriptions(raw_prescriptions)
    corrected_prescriptions = []
    
    for code in cleaned_prescriptions:
        expected_validation = str(calculate_validation_digit(code))
        
        corrected = False
        if code[-1] != expected_validation:
            code = code[:-1] + expected_validation
            corrected = True
        
        corrected_prescriptions.append(code)
        
        if corrected:
            print(f"{code} → Validation digit corrected")
        else:
            print(f"{code} → Validation digit already correct")
    
    return corrected_prescriptions
""",
    'g8_task4_w3': """
def prescription_report(raw_prescriptions):
    cleaned_prescriptions = extract_prescriptions(raw_prescriptions)

    correct = 0
    incorrect = 0

    for code in cleaned_prescriptions:
        expected_validation = str(calculate_validation_digit(code))
        actual_validation = code[-1]

        if actual_validation == expected_validation:
            correct += 1
        else:
            incorrect += 1

    total = correct + incorrect
    percentage_incorrect = (incorrect / total) * 100 if total > 0 else 0

    print(f"Number of correct codes: {correct}")
    print(f"Number of incorrect codes: {incorrect}")
    print(f"Percentage of incorrect codes: {percentage_incorrect}%")

prescription_report(raw_prescriptions)
""",
    'g8_task5_w3': """
def format_prescription(prescription_code):
    part1 = prescription_code[:2]      
    part2 = prescription_code[2:6]     
    part3 = prescription_code[6:-1]    
    check_char = prescription_code[-1] 

    formatted = f"{part1}-{part2}-{part3}{check_char}"
    return formatted
""",
    'g8_task6_w3': """
def add_medication_type(raw_prescriptions):
    cleaned_prescriptions = extract_prescriptions(raw_prescriptions)
    categorized_prescriptions = []

    for code in cleaned_prescriptions:
        prefix = code[:2]

        if prefix == "RX":
            med_type = "General Prescription"
        elif prefix == "AB":
            med_type = "Antibiotic"
        elif prefix in ["CD", "EF"]:
            med_type = "Controlled Substance"
        else:
            med_type = "Unknown"

        categorized_prescriptions.append((code, med_type))

    return categorized_prescriptions

add_medication_type(raw_prescriptions)
""",
    'g9_task1_w3': """
def extract_tickets(raw_tickets):
    cleaned_tickets = []

    for ticket in raw_tickets:
        invalid = False   
        cleaned = ""

        for c in ticket:
            if c == "&" or c == "^":
                invalid = True
                break

            if c == " " or c == "." or c == "-":
                continue

            cleaned += c

        if not invalid:
            cleaned_tickets.append(cleaned.upper())

    return cleaned_tickets
""",
    'g9_task2_w3': """
def calculate_control_digit(ticket_serial):
    first_10 = ticket_serial[:10]
    
    total = 0
    
    for char in first_10:
        if char.isdigit():       
            total += int(char)    
    
    control_digit = total % 10
    
    return control_digit
""",
    'g9_task3_w3': """
def correct_control_digits(raw_tickets):
    cleaned_tickets = extract_tickets(raw_tickets)
    corrected_tickets = []
    
    for code in cleaned_tickets:
        expected_control = str(calculate_control_digit(code))
        
        corrected = False
        if code[-1] != expected_control:
            code = code[:-1] + expected_control
            corrected = True
        
        corrected_tickets.append(code)
        
        if corrected:
            print(f"{code} → Control digit corrected")
        else:
            print(f"{code} → Control digit already correct")
    
    return corrected_tickets
""",
    'g9_task4_w3': """
def ticket_report(raw_tickets):
    cleaned_tickets = extract_tickets(raw_tickets)

    correct = 0
    incorrect = 0

    for code in cleaned_tickets:
        expected_control = str(calculate_control_digit(code))
        actual_control = code[-1]

        if actual_control == expected_control:
            correct += 1
        else:
            incorrect += 1

    total = correct + incorrect
    percentage_incorrect = (incorrect / total) * 100 if total > 0 else 0

    print(f"Number of correct codes: {correct}")
    print(f"Number of incorrect codes: {incorrect}")
    print(f"Percentage of incorrect codes: {percentage_incorrect}%")

ticket_report(raw_tickets)
""",
    'g9_task5_w3': """
def format_ticket(ticket_serial):
    part1 = ticket_serial[:3]      
    part2 = ticket_serial[3:7]     
    part3 = ticket_serial[7:-1]     
    check_char = ticket_serial[-1]  

    formatted = f"{part1}-{part2}-{part3}{check_char}"
    return formatted
""",
    'g9_task6_w3': """
def add_ticket_category(raw_tickets):
    cleaned_tickets = extract_tickets(raw_tickets)
    categorized_tickets = []

    for ticket in cleaned_tickets:
        prefix = ticket[:3]

        if prefix == "VIP":
            category = "VIP Access"
        elif prefix == "STD":
            category = "Standard"
        elif prefix == "PRE":
            category = "Premium"
        else:
            category = "Unknown"

        categorized_tickets.append((ticket, category))

    return categorized_tickets

add_ticket_category(raw_tickets)
""",
}