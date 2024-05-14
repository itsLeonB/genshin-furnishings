package model

import "go.mongodb.org/mongo-driver/bson/primitive"

type Material struct {
	ID       primitive.ObjectID `json:"id"`
	Name     string             `json:"name"`
	Quantity int                `json:"quantity"`
}
