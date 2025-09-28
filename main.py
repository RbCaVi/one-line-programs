import discord
from discord.ext import commands

# https://stackoverflow.com/a/71169236

guild_ids = [1203529312016400435] # just crest for now

def slash_command(name, *args, **kwargs):
  return bot.slash_command(*args, name = name, **kwargs)

bot = commands.Bot()

@slash_command('first_slash')
async def first_slash(ctx):
  await ctx.respond('You executed the slash command first_slash!')

@slash_command('create_project')
async def create_project(ctx):
  await ctx.respond('You executed the slash command create_project!')

@slash_command('add_statement')
async def add_statement(ctx):
  await ctx.respond('You executed the slash command add_statement!')

@slash_command('edit_statement')
async def edit_statement(ctx):
  await ctx.respond('You executed the slash command edit_statement!')

@slash_command('delete_statement')
async def delete_statement(ctx):
  await ctx.respond('You executed the slash command delete_statement!')

@slash_command('add_file')
async def add_file(ctx):
  await ctx.respond('You executed the slash command add_file!')

@slash_command('delete_file')
async def delete_file(ctx):
  await ctx.respond('You executed the slash command delete_file!')

@slash_command('show_files')
async def show_files(ctx):
  await ctx.respond('You executed the slash command show_files!')

@slash_command('view_file')
async def view_file(ctx):
  await ctx.respond('You executed the slash command view_file!')

@bot.event
async def on_ready() -> None:
  print(f"I am {bot.user}.")
  assert bot.user is not None
  print(f"Others may know me as {bot.user.display_name}.")
  print(f"ID: {bot.user.id}")

with open('token') as f:
  token = f.read()

bot.run(token)
