import discord
import discord.ext.commands
import contextlib
import json
import os
import random
import string

# https://stackoverflow.com/a/71169236

guild_ids = [1203529312016400435] # just crest for now
projects_info_path = 'projects.json'
files_path = 'files/'

@contextlib.contextmanager
def command_group(bot, name, **kwargs):
  group = bot.create_group(name = name, **kwargs)
  yield CommandGroup(group)

def slash_command(bot, name, **kwargs):
  return bot.slash_command(name = name, guild_ids = guild_ids, **kwargs)

class CommandGroup:
  def __init__(self, group):
    self.group = group

  @contextlib.contextmanager
  def command_group(self, name, **kwargs):
    group = self.group.create_subgroup(name = name, **kwargs)
    yield CommandGroup(group)

  def slash_command(self, name, **kwargs):
    return self.group.command(name = name, guild_ids = guild_ids, **kwargs)

class Projects:
  def __init__(self):
    self.projects = []
    try:
      with open(projects_info_path) as f:
        projects_data = json.load(f)
      self.projects = [Project.load(p) for p in projects_data]
    except Exception as e:
      print(f'Could not load projects from {projects_info_path}.')
      print(f'Error: {e}')
    self.projects_by_channel_id = {p.channel_id: p for p in self.projects}
    self.projects_by_name = {p.name: p for p in self.projects}

  def save(self):
    with open(projects_info_path, 'w') as f:
      json.dump([p.dump() for p in self.projects], f, indent = 2)

  def __contains__(self, project):
    if isinstance(project, int):
      return project in self.projects_by_channel_id
    if isinstance(project, str):
      return project in self.projects_by_name
    return (
      project.channel_id in self.projects_by_channel_id or
      project.name in self.projects_by_name
    )

  def add(self, project):
    assert project not in self
    self.projects.append(project)
    self.projects_by_channel_id[project.channel_id] = project
    self.projects_by_name[project.name] = project
    project.files.append(File.new('main'))

  def __getitem__(self, i):
    # get a project by either name or channel id
    if i in self.projects_by_channel_id:
      return self.projects_by_channel_id[i]
    elif i in self.projects_by_name:
      return self.projects_by_name[i]
    else:
      raise ValueError(f'No project exists for key {repr(i)}')

class Project:
  def __init__(self, name, channel_id, files):
    self.name = name
    self.channel_id = channel_id
    self.files = files

  @staticmethod
  def load(project_data):
    return Project(
      name = project_data['name'],
      channel_id = project_data['channel_id'],
      files = [File.load(f) for f in project_data['files']],
    )

  @staticmethod
  def new(name, channel):
    return Project(
      name = name,
      channel_id = ctx.channel.id,
      files = []
    )

  def dump(self):
    return {
      'name': self.name,
      'channel_id': self.channel_id,
      'files': [f.dump() for f in self.files],
    }

class File:
  def __init__(self, name, real_name):
    self.name = name
    self.real_name = real_name
    with open(os.path.join(files_path, self.real_name)) as f:
      lines_data = json.load(f)
    self.lines = [Line.load(l) for l in lines_data]

  @staticmethod
  def load(file_data):
    return File(
      name = file_data['name'],
      real_name = file_data['real_name'],
    )

  @staticmethod
  def new(name):
    # create an empty file
    # how do i generate a realname
    # idk just take name and put a "token" after it
    while os.path.exists(os.path.join(files_path, real_name := name + '_' + ''.join(random.choice(string.ascii_lowercase) for i in range(8)))): # this is the best way to write this
      pass
    with open(os.path.join(files_path, real_name), 'w') as f:
      json.dump([], f, indent = 2)
    return File(
      name = name,
      real_name = real_name,
    )

  def dump(self):
    return {
      'name': self.name,
      'real_name': self.real_name,
    }

  def save(self):
    with open(os.path.join(files_path, self.real_name), 'w') as f:
      json.dump([l.dump() for l in self.lines], f, indent = 2)

bot = discord.ext.commands.Bot()

projects = Projects()

@slash_command(bot, 'first_slash')
async def first_slash(ctx):
  await ctx.respond('You executed the slash command first_slash!')

with command_group(bot, 'project') as projectgroup:
  @projectgroup.slash_command('new')
  async def project_new(ctx, name: str):
    print(f'Attempting to create a project named `{name}` in channel id {ctx.channel.id} ({ctx.channel.name})')
    new_project = Project.new(name, ctx.channel)
    if new_project not in projects:
      projects.add(new_project)
      projects.save()
      await ctx.respond(f'Project `{new_project.name}` created.')
    else:
      if new_project.channel_id in projects:
        await ctx.respond(f'A project has already been created in this channel: `{projects[new_project.channel_id].name}`')
      elif new_project.name in projects:
        await ctx.respond(f'A project has already been created with this name in <#{projects[new_project.name].channel_id}>')

  @projectgroup.slash_command('files')
  async def project_files(ctx):
    if ctx.channel.id in projects:
      project = projects[ctx.channel.id]
      files = '\n'.join('`' + file.name + '`, (`' + file.real_name + '` internally)' for file in project.files)
      await ctx.respond(f'Project `{project.name}` has {len(project.files)} files:\n{files}')
    else:
      await ctx.respond('There is no project in this channel.')

with command_group(bot, 'file') as filegroup:
  @filegroup.slash_command('new')
  async def file_new(ctx):
    await ctx.respond('You executed the slash command add_file!')

  @filegroup.slash_command('delete')
  async def file_delete(ctx):
    await ctx.respond('You executed the slash command delete_file!')

  @filegroup.slash_command('view')
  async def file_view(ctx):
    await ctx.respond('You executed the slash command view_file!')

with command_group(bot, 'statement') as statementgroup:
  @statementgroup.slash_command('new')
  async def statement_new(ctx):
    await ctx.respond('You executed the slash command add_statement!')

  @statementgroup.slash_command('edit')
  async def statement_edit(ctx):
    await ctx.respond('You executed the slash command edit_statement!')

  @statementgroup.slash_command('delete')
  async def statement_delete(ctx):
    await ctx.respond('You executed the slash command delete_statement!')

@bot.event
async def on_ready() -> None:
  print(f"I am {bot.user}.")
  assert bot.user is not None
  print(f"Others may know me as {bot.user.display_name}.")
  print(f"ID: {bot.user.id}")

with open('token') as f:
  token = f.read()

bot.run(token)
