package model

import "go.mongodb.org/mongo-driver/bson/primitive"

type User struct {
	ID          primitive.ObjectID `json:"id"`
	Username    string             `json:"username"`
	Password    string             `json:"password"`
	Characters  []Character        `json:"characters"`
	Materials   []Material         `json:"materials"`
	Furnishings []Furnishing       `json:"furnishings"`
}
