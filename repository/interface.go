package repository

import (
	"context"

	"github.com/itsLeonB/genshin-furnishings/model"
)

type Repository interface {
	Register(ctx context.Context, in model.User) (string, error)
	Login(ctx context.Context, in model.User) (string, error)

	GetUser(ctx context.Context, username string) (model.User, error)
	CreateUser(ctx context.Context, in model.User) (model.User, error)
	UpdateUser(ctx context.Context, in model.User) (model.User, error)
	DeleteUser(ctx context.Context, username string) error
}
