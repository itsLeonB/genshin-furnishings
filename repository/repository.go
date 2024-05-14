package repository

import (
	"context"
	"errors"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"golang.org/x/crypto/bcrypt"

	"github.com/golang-jwt/jwt"
	"github.com/itsLeonB/genshin-furnishings/model"
)

var (
	ErrUserNotFound = errors.New("user not found")
	secretKey       = []byte("secret-key")
)

type repository struct {
	db *mongo.Database
}

func NewRepository(db *mongo.Database) Repository {
	return &repository{db: db}
}

func (r repository) Register(ctx context.Context, user model.User) (string, error) {
	hashedPassword, _ := bcrypt.GenerateFromPassword([]byte(user.Password), bcrypt.DefaultCost)
	user.Password = string(hashedPassword)

	out, err := r.db.
		Collection("users").
		InsertOne(ctx, fromModel(user))

	if err != nil {
		if mongo.IsDuplicateKeyError(err) {
			return "username already exists", nil
		}
		return "error registering, please try again", err
	}

	user.ID = out.InsertedID.(primitive.ObjectID)

	return "you are successfully registered, please login", nil
}

func (r repository) Login(ctx context.Context, in model.User) (string, error) {
	var out user
	err := r.db.
		Collection("users").
		FindOne(ctx, bson.M{"username": in.Username}).
		Decode(&out)

	if err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return "user not found", ErrUserNotFound
		}
		return "error logging in, please try again", err
	}

	err = bcrypt.CompareHashAndPassword([]byte(out.Password), []byte(in.Password))
	if err != nil {
		return "fail to login, please check your password", err
	}

	// return jwt token if success
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"username": out.Username,
	})

	tokenString, err := token.SignedString(secretKey)

	if err != nil {
		return "error logging in, please try again", err
	}

	return tokenString, nil
}

func (r repository) GetUser(ctx context.Context, username string) (model.User, error) {
	var out user
	err := r.db.
		Collection("users").
		FindOne(ctx, bson.M{"username": username}).
		Decode(&out)
	if err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return model.User{}, ErrUserNotFound
		}
		return model.User{}, err
	}
	return toModel(out), nil
}

func (r repository) CreateUser(ctx context.Context, user model.User) (model.User, error) {
	out, err := r.db.
		Collection("users").
		InsertOne(ctx, fromModel(user))
	if err != nil {
		return model.User{}, err
	}
	user.ID = out.InsertedID.(primitive.ObjectID)
	return user, nil
}

func (r repository) UpdateUser(ctx context.Context, user model.User) (model.User, error) {
	in := bson.M{}
	if user.Username != "" {
		in["username"] = user.Username
	}
	if user.Password != "" {
		in["password"] = user.Password
	}
	out, err := r.db.
		Collection("users").
		UpdateOne(ctx, bson.M{"email": user.Username}, bson.M{"$set": in})
	if err != nil {
		return model.User{}, err
	}
	if out.MatchedCount == 0 {
		return model.User{}, ErrUserNotFound
	}
	return user, nil
}

func (r repository) DeleteUser(ctx context.Context, username string) error {
	out, err := r.db.
		Collection("users").
		DeleteOne(ctx, bson.M{"username": username})
	if err != nil {
		return err
	}
	if out.DeletedCount == 0 {
		return ErrUserNotFound
	}
	return nil
}

type user struct {
	ID       primitive.ObjectID `bson:"_id,omitempty"`
	Username string             `bson:"username,omitempty"`
	Password string             `bson:"password,omitempty"`
}

func fromModel(in model.User) user {
	return user{
		Username: in.Username,
		Password: in.Password,
	}
}

func toModel(in user) model.User {
	return model.User{
		ID:       in.ID,
		Username: in.Username,
		Password: in.Password,
	}
}
